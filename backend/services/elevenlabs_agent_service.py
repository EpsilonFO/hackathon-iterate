import json
import os
import signal
import threading
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

from backend.services.conversation_manager import (
    ConversationStatus,
    conversation_manager,
)

# Load environment variables
load_dotenv()

# Store messages globally
messages = []
conversation_instance = None  # Store conversation instance globally
current_supplier_name = "Inconnu"  # Store current supplier name for callbacks

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
        "understood",
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
    global messages, conversation_instance, current_supplier_name
    messages = []
    current_supplier_name = supplier_name

    # Initialize client
    if api_key is None:
        api_key = os.environ.get("ELEVENLABS_API_KEY")

    client = ElevenLabs(api_key=api_key)

    # Start conversation with the agent using callbacks to capture transcript
    if agent_name == "delivery":
        agent_id = os.getenv("AGENT_DELIVERY_ID")
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
    conversation.start_session()

    # Wait for conversation to complete
    conversation_id = conversation.wait_for_session_end()

    print("\n\nConversation ended!")
    print(f"Conversation ID: {conversation_id}")

    return {
        "conversation_id": conversation_id,
        "supplier_name": supplier_name,
        "agent_id": agent_id,
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
    global messages, current_supplier_name

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
        save_transcript_on_exit(current_supplier_name)
        exit(0)


def save_transcript(
    transcript_data: dict, filename: str = None, folder: str = "./data/transcripts"
):
    """Save the transcript to a JSON file in the transcripts folder."""
    # Create transcripts folder if it doesn't exist
    os.makedirs(folder, exist_ok=True)

    if filename is None:
        # Use conversation_id from ElevenLabs (format: conv_xxxxx)
        conversation_id = transcript_data.get("conversation_id", None)

        if conversation_id and conversation_id != "unknown":
            filename = f"{folder}/{conversation_id}.json"
        else:
            # Fallback to timestamp if no conversation_id
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{folder}/transcript_{session_id}.json"

    with open(filename, "w") as f:
        json.dump(transcript_data, f, indent=2, default=str)

    print(f"\n✓ Transcript saved to {filename}")
    return filename


def save_transcript_on_exit(supplier_name: str = "Inconnu"):
    """Save transcript when interrupted"""
    global messages
    if messages:
        # Generate a session ID based on timestamp
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        result = {
            "conversation_id": session_id,
            "supplier_name": supplier_name,
            "agent_id": os.getenv("AGENT_PRODUCTS_ID"),
            "timestamp": datetime.now().isoformat(),
            "messages": messages,
            "total_messages": len(messages),
        }
        save_transcript(result)
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

        # Update status to completed
        conversation_manager.update_task_status(
            task_id,
            ConversationStatus.COMPLETED,
            conversation_id=result.get("conversation_id"),
            total_messages=result.get("total_messages", 0),
        )

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
