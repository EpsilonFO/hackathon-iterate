import json
import os
import signal
import threading
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

from backend.services.conversation_manager import (
    ConversationStatus,
    conversation_manager,
)
from backend.services.order_delivery_parser_service import OrderDeliveryParser
from backend.services.order_updater_service import OrderUpdater
from backend.services.transcript_parser_service import TranscriptParserService

# Load environment variables
load_dotenv()

# Store messages globally
messages = []
conversation_instance = None  # Store conversation instance globally
current_supplier_name = "Inconnu"  # Store current supplier name for callbacks
current_agent_name = "products"  # Store current agent name for callbacks
transcript_saved = False  # Flag to prevent duplicate transcript saves

# Goodbye keywords to detect end of conversation
GOODBYE_KEYWORDS = [
    "goodbye",
    "bye",
    "see you",
    "talk soon",
    "have a nice day",
    "take care",
    "thanks for calling",
    "end call",
    "bye-bye",
    "talk to you later",
]


def should_end_conversation(text: str) -> bool:
    """
    Check if the agent's message indicates the conversation should end.
    Only end if goodbye is at the end of the sentence or is a clear farewell.
    """
    text_lower = text.lower().strip()

    # Check if goodbye appears at the end of the message (last 50 characters)
    last_part = text_lower[-50:] if len(text_lower) > 50 else text_lower

    # Check for clear goodbye patterns
    goodbye_patterns = [
        "goodbye.",
        "goodbye!",
        "bye.",
        "bye!",
        "talk soon.",
        "talk soon!",
        "take care.",
        "take care!",
        "have a nice day.",
        "have a nice day!",
        "see you.",
        "see you!",
        "thanks for calling.",
        "thanks for calling!",
        "thank you for your time.",
        "thank you for your time!",
        "understood. thank you",
        "i understand you need to go",
    ]

    # Check if message ends with a goodbye pattern
    for pattern in goodbye_patterns:
        if last_part.endswith(pattern.rstrip(".!")):
            return True

    # Check if the entire message is just a short goodbye/acknowledgment
    short_endings = [
        "thank you for your time",
        "i understand you need to go",
        "thanks for your time",
    ]

    if len(text_lower.split()) <= 8:  # Short message
        for ending in short_endings:
            if ending in text_lower:
                return True
        for keyword in GOODBYE_KEYWORDS:
            if keyword in text_lower:
                return True

    return False


def make_outbound_call(
    agent_id: str, agent_phone_number_id: str, to_number: str, api_key: str = None
):
    """
    Make an outbound call using ElevenLabs Conversational AI via Twilio.

    Args:
        agent_id: The ID of your ElevenLabs agent
        agent_phone_number_id: The ID of your Twilio phone number in ElevenLabs
        to_number: The phone number to call (E.164 format, e.g., +15551234567)
        api_key: Your ElevenLabs API key (or set ELEVENLABS_API_KEY env var)

    Returns:
        dict: Call information
    """
    if api_key is None:
        api_key = os.environ.get("ELEVENLABS_API_KEY")

    if not api_key:
        raise ValueError(
            "ELEVENLABS_API_KEY must be set in .env or passed as parameter"
        )

    # Initialize ElevenLabs client
    client = ElevenLabs(api_key=api_key)

    print("Making outbound call...")
    print(f"  Agent ID: {agent_id}")
    print(f"  Agent Phone Number ID: {agent_phone_number_id}")
    print(f"  To Number: {to_number}")

    # Make the outbound call
    result = client.conversational_ai.twilio.outbound_call(
        agent_id=agent_id,
        agent_phone_number_id=agent_phone_number_id,
        to_number=to_number,
    )

    print("\n✓ Call initiated successfully!")
    print(f"  Result: {result}")

    # Try to get call_id if it exists as an attribute
    if hasattr(result, "call_id"):
        print(f"  Call ID: {result.call_id}")
    elif hasattr(result, "conversation_id"):
        print(f"  Conversation ID: {result.conversation_id}")

    return result


def call_agent(
    agent_name: str,
    api_key: str = None,
    supplier_name: str = "Inconnu",
    enable_signal_handler: bool = True,
):
    """
    Call an ElevenLabs conversational agent and return the transcript.

    Args:
        agent_name: The name of the agent (e.g., "delivery" or "products")
        api_key: Your ElevenLabs API key (or set ELEVENLABS_API_KEY env var)
        supplier_name: Name of the supplier
        enable_signal_handler: Whether to enable Ctrl+C handler (only works in main thread)

    Returns:
        dict: Conversation transcript with messages
    """
    global \
        messages, \
        conversation_instance, \
        current_supplier_name, \
        current_agent_name, \
        transcript_saved
    messages = []
    current_supplier_name = supplier_name
    current_agent_name = agent_name
    transcript_saved = False  # Reset flag for new conversation

    # Initialize client
    if api_key is None:
        api_key = os.environ.get("ELEVENLABS_API_KEY")

    client = ElevenLabs(api_key=api_key)

    # Start conversation with the agent using callbacks to capture transcript
    if agent_name == "delivery":
        agent_id = os.getenv("AGENT_DELIVERY_ID")
    elif agent_name == "availability":
        agent_id = os.getenv("AGENT_AVAILABILITY_ID")
    else:  # agent_name == "products":
        agent_id = os.getenv("AGENT_PRODUCTS_ID")

    conversation = Conversation(
        client=client,
        agent_id=agent_id,
        requires_auth=bool(api_key),
        audio_interface=DefaultAudioInterface(),
        # Callbacks to capture the conversation
        callback_agent_response=lambda response: capture_agent_message(
            response, conversation
        ),
        callback_user_transcript=lambda transcript: capture_message("user", transcript),
    )

    conversation_instance = conversation

    print("Starting conversation with agent...")
    print("Speak to begin. Say 'goodbye' to end the conversation, or press Ctrl+C.\n")

    # Handle Ctrl+C gracefully to save transcript before exit
    # Only set signal handler if running in main thread
    if enable_signal_handler:

        def signal_handler(sig, frame):
            print("\n\nEnding conversation...")
            try:
                conversation.end_session()
            except:
                pass
            # Save transcript immediately
            save_transcript_on_exit(supplier_name)
            exit(0)

        try:
            signal.signal(signal.SIGINT, signal_handler)
        except ValueError:
            # Signal handler can't be set in non-main thread, which is fine
            print("(Running in background thread - Ctrl+C handler disabled)")

    # Start the conversation
    AGENT_PHONE_NUMBER_ID = os.getenv(
        "TWILIO_PHONE_NUMBER_ID"
    )  # You need to ad d this to .env
    TO_NUMBER = os.getenv("MY_PHONE_NUMBER")  # You need to add this to .env
    make_outbound_call(
        agent_id=agent_id,
        agent_phone_number_id=AGENT_PHONE_NUMBER_ID,
        to_number=TO_NUMBER,
    )
    # conversation.start_session()

    # Wait for conversation to complete
    conversation_id = conversation.wait_for_session_end()

    print("\n\nConversation ended!")
    print(f"Conversation ID: {conversation_id}")

    # If transcript was already saved (e.g., on interrupt), don't save again
    # The conversation_id from ElevenLabs will be used when saving in call_agent_background
    return {
        "conversation_id": conversation_id,
        "supplier_name": supplier_name,
        "agent_id": agent_id,
        "agent_name": agent_name,
        "timestamp": datetime.now().isoformat(),
        "messages": messages,
        "total_messages": len(messages),
    }


def capture_message(role: str, text: str):
    """Callback function to capture messages"""
    global messages
    message = {"role": role, "text": text}
    messages.append(message)
    print(f"[{role.upper()}]: {text}")


def capture_agent_message(text: str, conversation):
    """Callback function to capture agent messages and detect goodbye"""
    global messages, current_supplier_name, transcript_saved

    # Capture the message
    message = {"role": "agent", "text": text}
    messages.append(message)
    print(f"[AGENT]: {text}")

    # Check if agent said goodbye in a way that ends the conversation
    if should_end_conversation(text):
        print("\n🔔 Agent said goodbye - ending conversation...")
        # Give a brief moment for the audio to finish
        import time

        time.sleep(2)
        try:
            conversation.end_session()
        except Exception as e:
            print(f"Note: {e}")
        # Don't save transcript here - let call_agent_background save it with the real conversation_id
        # The conversation.end_session() above will cause wait_for_session_end() to return


def save_transcript(
    transcript_data: dict, filename: str = None, folder: str = "./data/transcripts"
):
    """Save the transcript to a JSON file in the transcripts folder."""
    # Create transcripts folder if it doesn't exist
    os.makedirs(folder, exist_ok=True)

    if filename is None:
        # Always use timestamp format for filename (YYYYMMDD_HHMMSS)
        # Use timestamp from transcript_data if available, otherwise use current time
        timestamp_str = transcript_data.get("timestamp", None)
        if timestamp_str:
            try:
                # Parse the ISO timestamp and format it
                dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                session_id = dt.strftime("%Y%m%d_%H%M%S")
            except Exception:
                # Fallback to current time if parsing fails
                session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"{folder}/{session_id}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(transcript_data, f, indent=2, default=str)

    print(f"\n✓ Transcript saved to {filename}")
    return filename


def save_transcript_on_exit(supplier_name: str = "Inconnu"):
    """Save transcript when interrupted"""
    global messages, current_agent_name, transcript_saved
    if transcript_saved:
        print("\n! Transcript already saved, skipping duplicate save")
        return
    if messages:
        # Generate a session ID based on timestamp
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        result = {
            "conversation_id": session_id,
            "supplier_name": supplier_name,
            "agent_id": os.getenv("AGENT_PRODUCTS_ID"),
            "agent_name": current_agent_name,
            "timestamp": datetime.now().isoformat(),
            "messages": messages,
            "total_messages": len(messages),
        }
        save_transcript(result)
        transcript_saved = True
        print(f"✓ Messages captured in this conversation: {len(messages)}")
    else:
        print("\n! No messages to save")


def call_agent_background(
    task_id: str, agent_name: str, api_key: str, supplier_name: str
):
    """
    Execute call_agent in a background thread and update task status.

    Args:
        task_id: ID of the task to track
        agent_name: Name of the agent to call
        api_key: ElevenLabs API key
        supplier_name: Name of the supplier
    """
    try:
        # Update status to running
        conversation_manager.update_task_status(task_id, ConversationStatus.RUNNING)

        # Call the agent (this will block in this thread, but not the main FastAPI thread)
        # Disable signal handler since we're in a background thread
        result = call_agent(
            agent_name,
            api_key=api_key,
            supplier_name=supplier_name,
            enable_signal_handler=False,
        )

        # Save the transcript to file only if it hasn't been saved already
        # (e.g., if save_transcript_on_exit was called when agent said goodbye)
        global transcript_saved
        if not transcript_saved:
            # Ensure supplier_name is preserved from the result (in case it was modified)
            transcript_data = {
                "conversation_id": result.get("conversation_id"),
                "supplier_name": result.get("supplier_name", supplier_name),
                "agent_id": result.get("agent_id"),
                "agent_name": agent_name,
                "timestamp": result.get("timestamp"),
                "messages": result.get("messages", []),
                "total_messages": result.get("total_messages", 0),
            }
            save_transcript(transcript_data)
            transcript_saved = True
        else:
            print("✓ Transcript already saved (skipping duplicate)")

        # Update status to completed
        conversation_manager.update_task_status(
            task_id,
            ConversationStatus.COMPLETED,
            conversation_id=result.get("conversation_id"),
            total_messages=result.get("total_messages", 0),
        )

        # Automatically parse the conversation and update CSVs based on agent type
        try:
            anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            if not anthropic_api_key:
                print("⚠ ANTHROPIC_API_KEY not set, skipping automatic parsing")
            else:
                # Get the saved transcript data
                transcript_data = {
                    "conversation_id": result.get("conversation_id"),
                    "supplier_name": result.get("supplier_name", supplier_name),
                    "agent_id": result.get("agent_id"),
                    "agent_name": agent_name,
                    "timestamp": result.get("timestamp"),
                    "messages": result.get("messages", []),
                    "total_messages": result.get("total_messages", 0),
                }

                # Route to appropriate parser based on agent type
                if agent_name == "delivery":
                    # Format transcript as text string for delivery parser
                    transcript_text = "\n\n".join(
                        [
                            f"{msg.get('role', 'unknown').capitalize()}: {msg.get('text', '')}"
                            for msg in result.get("messages", [])
                        ]
                    )

                    parser = OrderDeliveryParser(api_key=anthropic_api_key)
                    parsed_updates = parser.parse_conversation(
                        transcript=transcript_text,
                        supplier_name=result.get("supplier_name", supplier_name),
                    )

                    if parsed_updates:
                        # Load supplier mapping
                        supplier_df = pd.read_csv("./data/fournisseur.csv")
                        supplier_mapping = dict(
                            zip(supplier_df["name"], supplier_df["id"])
                        )

                        # Apply updates to orders.csv
                        updater = OrderUpdater(csv_path="./data/orders.csv")
                        updater.load_csv()
                        successes, failures = updater.apply_updates(
                            parsed_updates, supplier_mapping
                        )
                        updater.save_csv()

                        print(
                            f"✓ Automatically parsed delivery conversation and updated orders.csv. Found {len(parsed_updates)} order update(s)."
                        )
                        if successes:
                            print(f"✓ {len(successes)} update(s) applied successfully")
                        if failures:
                            print(f"⚠ {len(failures)} update(s) failed: {failures}")
                    else:
                        print(
                            "✓ Delivery conversation parsed but no order updates found."
                        )

                elif agent_name == "products":
                    # Use TranscriptParserService for product conversations

                    parser = TranscriptParserService(
                        api_key=anthropic_api_key, data_dir="./data"
                    )
                    parsed_result = parser.parse_and_update_csv(
                        transcript_data,
                        result.get("supplier_name", supplier_name),
                        save=True,
                    )
                    print(
                        f"✓ Automatically parsed product conversation and updated CSV. Found {len(parsed_result)} product(s) to update."
                    )

                elif agent_name == "availability":
                    # Skip parsing for availability conversations
                    print("✓ Availability conversation completed (no parsing needed).")

                else:
                    print(
                        f"⚠ Unknown agent type '{agent_name}', skipping automatic parsing"
                    )

        except Exception as parse_error:
            # Don't fail the conversation if parsing fails - just log it
            print(
                f"⚠ Error during automatic parsing (conversation still marked as completed): {parse_error}"
            )
            import traceback

            traceback.print_exc()

    except Exception as e:
        # Update status to failed
        conversation_manager.update_task_status(
            task_id, ConversationStatus.FAILED, error=str(e)
        )
        print(f"Error in background conversation: {e}")


def start_agent_async(
    agent_name: str, api_key: str = None, supplier_name: str = "Inconnu"
) -> str:
    """
    Start an agent conversation asynchronously in a background thread.

    Args:
        agent_name: Name of the agent to call
        api_key: ElevenLabs API key (or set ELEVENLABS_API_KEY env var)
        supplier_name: Name of the supplier

    Returns:
        str: Task ID to track the conversation status
    """
    if api_key is None:
        api_key = os.environ.get("ELEVENLABS_API_KEY")

    # Create a task
    task = conversation_manager.create_task(agent_name, supplier_name)

    # Start the conversation in a background thread
    thread = threading.Thread(
        target=call_agent_background,
        args=(task.task_id, agent_name, api_key, supplier_name),
        daemon=True,
    )
    thread.start()

    return task.task_id
