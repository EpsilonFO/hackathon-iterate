"""Controller for parsing phone conversation transcripts related to order deliveries."""

from typing import Dict
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from backend.services.order_delivery_parser_service import OrderDeliveryParser


router = APIRouter(prefix="/order-parser", tags=["order-parser"])


class OrderConversationRequest(BaseModel):
    """Request model for order conversation parsing."""

    transcript: str
    supplier_name: str


class OrderConversationResponse(BaseModel):
    """Response model for order conversation parsing."""

    updates: Dict[str, Dict[str, any]]
    message: str


@router.post("/parse-delivery-updates", response_model=OrderConversationResponse)
async def parse_delivery_updates(request: OrderConversationRequest):
    """
    Parse a phone conversation transcript to extract order delivery updates.

    Args:
        request: OrderConversationRequest containing transcript and supplier_name

    Returns:
        OrderConversationResponse with extracted delivery updates

    Example request:
    ```json
    {
        "transcript": "Bonjour, la commande de Paracétamol 500mg sera livrée le 20 décembre au lieu du 15.",
        "supplier_name": "Pharma Depot"
    }
    ```

    Example response:
    ```json
    {
        "updates": {
            "[Paracétamol 500mg, Pharma Depot]": {
                "new_date": "2025-12-20",
                "delay_days": 5
            }
        },
        "message": "Successfully parsed 1 order delivery update(s)"
    }
    ```
    """
    try:
        parser = OrderDeliveryParser()
        updates = parser.parse_conversation(
            transcript=request.transcript, supplier_name=request.supplier_name
        )

        count = len(updates)
        message = f"Successfully parsed {count} order delivery update(s)"

        return OrderConversationResponse(updates=updates, message=message)

    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error parsing conversation: {str(e)}"
        )
