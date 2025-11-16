import json
import os
import threading
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

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
    agent_id: str,
    agent_phone_number_id: str,
    to_number: str,
    api_key: str = None,
    supplier_name: str = "Inconnu",
    wait_for_completion: bool = False,
    auto_save_transcript: bool = True,
):
    """
    Make an outbound call using ElevenLabs Conversational AI via Twilio.

    Args:
        agent_id: The ID of your ElevenLabs agent
        agent_phone_number_id: The ID of your Twilio phone number in ElevenLabs
        to_number: The phone number to call (E.164 format, e.g., +15551234567)
        api_key: Your ElevenLabs API key (or set ELEVENLABS_API_KEY env var)
        supplier_name: Name of the supplier for the transcript
        wait_for_completion: If True, wait for the call to complete before returning
        auto_save_transcript: If True, automatically save transcript when call completes

    Returns:
        dict: Call information including conversation_id
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

    # Extract call_sid and conversation_id
    call_sid = None
    conversation_id = None

    if hasattr(result, "call_sid"):
        call_sid = result.call_sid
        print(f"  Call SID: {call_sid}")

    if hasattr(result, "call_id"):
        conversation_id = result.call_id
        print(f"  Call ID (Conversation ID): {conversation_id}")
    elif hasattr(result, "conversation_id"):
        conversation_id = result.conversation_id
        print(f"  Conversation ID: {conversation_id}")

    print("\n⏳ The call is now active on Twilio.")

    # If wait_for_completion is True, poll Twilio until call is done
    if wait_for_completion and call_sid:
        import time

        from twilio.rest import Client as TwilioClient

        twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")

        if not twilio_account_sid or not twilio_auth_token:
            print("\n⚠️  Warning: TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not set.")
            print("   Cannot monitor call status. Returning immediately.")
        else:
            twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token)

            print("\n⏳ Waiting for call to complete...")
            print("   Monitoring Twilio call status (checking every 5 seconds)")

            max_wait_time = 600  # 10 minutes max
            check_interval = 5  # Check every 5 seconds
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                time.sleep(check_interval)
                elapsed_time += check_interval

                try:
                    # Get call status from Twilio
                    call = twilio_client.calls(call_sid).fetch()
                    status = call.status

                    print(f"   Call status: {status} ({elapsed_time}s elapsed)")

                    # Check if call is completed
                    # Possible statuses: queued, ringing, in-progress, completed, busy, failed, no-answer, canceled
                    if status in [
                        "completed",
                        "busy",
                        "failed",
                        "no-answer",
                        "canceled",
                    ]:
                        print(f"\n✓ Call ended with status: {status}")

                        # Wait a bit more for ElevenLabs to process the transcript
                        print("   Waiting 1 second for transcript to be processed...")
                        time.sleep(1)

                        if auto_save_transcript and conversation_id:
                            # Try to fetch and save the transcript from ElevenLabs
                            try:
                                print("   Fetching transcript from ElevenLabs...")

                                # Try using conversational_ai.conversations.get to get conversation details
                                try:
                                    conv_details = (
                                        client.conversational_ai.conversations.get(
                                            conversation_id=conversation_id
                                        )
                                    )
                                    print("   ✓ Conversation details retrieved!")

                                    # Extract messages from transcript
                                    messages = []
                                    if (
                                        hasattr(conv_details, "transcript")
                                        and conv_details.transcript
                                    ):
                                        for turn in conv_details.transcript:
                                            if hasattr(turn, "role") and hasattr(
                                                turn, "message"
                                            ):
                                                messages.append(
                                                    {
                                                        "role": turn.role,
                                                        "text": turn.message,
                                                    }
                                                )

                                    print(
                                        f"   ✓ Extracted {len(messages)} messages from transcript"
                                    )

                                    transcript_result = {
                                        "conversation_id": conversation_id,
                                        "supplier_name": supplier_name,
                                        "agent_id": agent_id,
                                        "timestamp": datetime.now().isoformat(),
                                        "messages": messages,
                                        "total_messages": len(messages),
                                    }
                                    save_transcript(transcript_result)
                                except Exception as inner_e:
                                    print(f"   ⚠️  Could not get signed URL: {inner_e}")

                                    # Save minimal call info
                                    print(
                                        "   Saving call info without full transcript..."
                                    )
                                    transcript_result = {
                                        "conversation_id": conversation_id,
                                        "supplier_name": supplier_name,
                                        "agent_id": agent_id,
                                        "timestamp": datetime.now().isoformat(),
                                        "call_sid": call_sid,
                                        "call_status": status,
                                        "status": "completed",
                                        "note": f"View transcript in ElevenLabs dashboard with ID: {conversation_id}",
                                    }
                                    save_transcript(transcript_result)

                            except Exception as e:
                                print(f"   ⚠️  Error fetching transcript: {e}")
                                print("   Saving call info...")

                                # Always save call info
                                transcript_result = {
                                    "conversation_id": conversation_id,
                                    "supplier_name": supplier_name,
                                    "agent_id": agent_id,
                                    "timestamp": datetime.now().isoformat(),
                                    "call_sid": call_sid,
                                    "call_status": status,
                                    "status": "completed",
                                }
                                save_transcript(transcript_result)

                        return {
                            "conversation_id": conversation_id,
                            "supplier_name": supplier_name,
                            "agent_id": agent_id,
                            "timestamp": datetime.now().isoformat(),
                            "call_sid": call_sid,
                            "call_status": status,
                            "status": "completed",
                        }

                except Exception as e:
                    print(f"   Error checking Twilio status: {e}")

            print("\n⚠️  Maximum wait time reached.")

    return {
        "conversation_id": conversation_id,
        "supplier_name": supplier_name,
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat(),
        "call_sid": call_sid,
        "status": "call_initiated",
    }


def call_agent(
    agent_name: str,
    api_key: str = None,
    supplier_name: str = "Inconnu",
    enable_signal_handler: bool = True,
):
    """
    Call an ElevenLabs conversational agent via Twilio outbound call.

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

    # Get agent ID based on agent name
    if agent_name == "delivery":
        agent_id = os.getenv("AGENT_DELIVERY_ID")
    elif agent_name == "availability":
        agent_id = os.getenv("AGENT_AVAILABILITY_ID")
    else:  # agent_name == "products":
        agent_id = os.getenv("AGENT_PRODUCTS_ID")

    # Get Twilio configuration
    agent_phone_number_id = os.getenv("TWILIO_PHONE_NUMBER_ID")
    to_number = os.getenv("MY_PHONE_NUMBER")

    print(f"📞 Starting Twilio outbound call for {agent_name} agent...")
    print(f"   Calling: {to_number}")
    print(f"   Supplier: {supplier_name}\n")

    # Make the outbound call with automatic transcript saving
    result = make_outbound_call(
        agent_id=agent_id,
        agent_phone_number_id=agent_phone_number_id,
        to_number=to_number,
        api_key=api_key,
        supplier_name=supplier_name,
        wait_for_completion=True,
        auto_save_transcript=True,
    )
    result["agent_name"] = agent_name

    print("\n✓ Call completed!")
    print(f"  Conversation ID: {result.get('conversation_id')}")

    return result


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
