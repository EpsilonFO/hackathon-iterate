"""Controller for parsing phone conversation transcripts."""

from typing import Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.transcript_parser_service import TranscriptParserService

router = APIRouter(prefix="/parser", tags=["parser"])


class ConversationRequest(BaseModel):
    """Request model for conversation parsing."""

    transcript: str
    supplier_name: str | None = None


class ConversationResponse(BaseModel):
    """Response model for conversation parsing."""

    updates: Dict[str, Dict[str, float]]
    message: str


@router.post("/parse-conversation", response_model=ConversationResponse)
async def parse_conversation(request: ConversationRequest):
    """
    Parse a phone conversation transcript to extract product updates.

    Args:
        request: ConversationRequest containing transcript and supplier_name

    Returns:
        ConversationResponse with extracted product updates

    Example request:
    ```json
    {
        "transcript": "Bonjour, pour le Paracétamol 500mg, nous pouvons vous le proposer à 3.50 euros avec livraison en 7 jours.",
        "supplier_name": "Pharma Depot"
    }
    ```

    Example response:
    ```json
    {
        "updates": {
            "[Paracétamol 500mg, Pharma Depot]": {
                "price": 3.50,
                "delivery_time": 7
            }
        },
        "message": "Successfully parsed 1 product update(s)"
    }
    ```
    """
    try:
        parser = TranscriptParserService()
        updates = parser.parse_conversation(
            transcript=request.transcript,
            supplier_name=request.supplier_name or "Inconnu",
        )

        count = len(updates)
        message = f"Successfully parsed {count} product update(s)"

        return ConversationResponse(updates=updates, message=message)

    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error parsing conversation: {str(e)}"
        )
