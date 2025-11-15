"""Controller for ElevenLabs agent service endpoints."""

import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.transcript_parser_service import TranscriptParserService

load_dotenv()

router = APIRouter(prefix="/api/agent", tags=["agent"])


class StartConversationRequest(BaseModel):
    """Request model for starting a conversation."""

    agent_id: Optional[str] = None
    api_key: Optional[str] = None
    supplier_name: Optional[str] = None


class ConversationResponse(BaseModel):
    """Response model for conversation result."""

    conversation_id: str
    agent_id: str
    timestamp: str
    total_messages: int


@router.post("/start", response_model=ConversationResponse)
async def start_conversation(request: StartConversationRequest):
    """
    Launch the agent discussion pipeline, save the transcript and return the result.

    Args:
        request: StartConversationRequest with optional agent_id and api_key

    Returns:
        ConversationResponse with conversation details and saved transcript filename
    """
    print("Starting conversation...")
    agent_id = request.agent_id or os.getenv("AGENT_ID")
    api_key = request.api_key or os.getenv("ELEVENLABS_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    parser = TranscriptParserService(api_key=anthropic_api_key, data_dir="./data")

    if not agent_id or not api_key:
        raise HTTPException(
            status_code=400,
            detail="Missing AGENT_ID or ELEVENLABS_API_KEY. Please provide in request or set as environment variables.",
        )

    try:
        # Launch the agent conversation
        supplier_name = request.supplier_name or "Inconnu"
        # result = call_agent(agent_id, api_key=api_key, supplier_name=supplier_name)
        result = {
            "conversation_id": "20251115_211355",
            "supplier_name": "Inconnu",
            "agent_id": "agent_5401ka49jhknfwcraz1c3jgwpf7a",
            "timestamp": "2025-11-15T21:13:55.999015",
            "messages": [
                {
                    "role": "agent",
                    "text": "Hey there, I'm Alexis, the assistant of the pharmacy. Who's there ?",
                },
                {
                    "role": "user",
                    "text": "The assistant of the pharmacy. Who's there? Hello. I have a new product. It's dentifrice. It costs five euros and it takes two days to get delivered.",
                },
                {"role": "agent", "text": "Hello! Thanks for..."},
                {"role": "user", "text": "Oh, thanks for reaching out."},
                {"role": "agent", "text": "Thanks for reaching out with..."},
                {"role": "user", "text": "For reaching out with that offer."},
                {
                    "role": "agent",
                    "text": "Okay, so dentifrice at five euros with two day delivery. Let me ask you a few quick questions to evaluate this properly. First, what's the wholesale price per unit, and is there a minimum order quantity I need to meet? Also, do you offer any bulk discounts or promotional pricing for larger orders?",
                },
                {"role": "user", "text": "No, goodbye."},
                {"role": "agent", "text": "Goodbye!"},
            ],
            "total_messages": 9,
        }
        # Parse the conversation - pass the full result dict, not just messages
        _ = parser.parse_and_update_csv(result, supplier_name, save=True)

        return ConversationResponse(
            conversation_id=result["conversation_id"],
            agent_id=result["agent_id"],
            timestamp=result["timestamp"],
            total_messages=result["total_messages"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting conversation: {str(e)}",
        ) from e
