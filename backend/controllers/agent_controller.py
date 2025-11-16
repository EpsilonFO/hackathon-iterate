"""Controller for ElevenLabs agent service endpoints."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.controllers.update_agent import update_agent
from backend.services.conversation_manager import conversation_manager
from backend.services.elevenlabs_agent_service import start_agent_async
from backend.services.transcript_parser_service import TranscriptParserService

# Default transcripts directory
TRANSCRIPTS_DIR = Path("./data/transcripts")

load_dotenv()

router = APIRouter(prefix="/api/agent", tags=["agent"])


class StartConversationRequest(BaseModel):
    """Request model for starting a conversation."""

    agent_name: Optional[str] = None
    api_key: Optional[str] = None
    supplier_name: Optional[str] = None
    product_name: Optional[str] = None


class ConversationResponse(BaseModel):
    """Response model for conversation result."""

    conversation_id: str
    agent_name: str
    timestamp: str
    total_messages: int


class TaskStartResponse(BaseModel):
    """Response model when starting an async conversation."""

    task_id: str
    agent_name: str
    supplier_name: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """Response model for task status."""

    task_id: str
    agent_name: str
    supplier_name: str
    status: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    conversation_id: Optional[str]
    error: Optional[str]
    total_messages: int


class ActivitySummaryResponse(BaseModel):
    """Response model for agent activity summary."""

    delivery_risks_resolved: int
    supplier_followups_sent: int
    price_checks_completed: int
    new_product_matches: int
    time_saved_minutes: int


class ActivityItem(BaseModel):
    """Model for individual activity item in recap."""

    task_id: str
    agent_name: str
    supplier_name: str
    status: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    conversation_id: Optional[str]
    error: Optional[str]
    total_messages: int
    task_type: (
        str  # "delivery_risk", "price_update", "supplier_followup", "product_discovery"
    )
    description: Optional[str] = None


class ActivityRecapResponse(BaseModel):
    """Response model for activity recap."""

    activities: List[ActivityItem]
    total_count: int


class TranscriptResponse(BaseModel):
    """Response model for transcript."""

    conversation_id: str
    supplier_name: str
    agent_id: Optional[str]
    timestamp: str
    messages: List[dict]
    total_messages: int
    formatted_text: str


@router.post("/start", response_model=TaskStartResponse)
async def start_conversation(request: StartConversationRequest):
    """
    Launch the agent discussion pipeline asynchronously in the background.

    This endpoint returns immediately with a task_id that can be used to track
    the conversation status using the /status/{task_id} endpoint.

    Args:
        request: StartConversationRequest with optional agent_name, api_key, and supplier_name

    Returns:
        TaskStartResponse with task_id to track the conversation
    """
    print("Starting conversation asynchronously...")
    agent_name = request.agent_name or "products"  # Default agent name
    api_key = request.api_key or os.getenv("ELEVENLABS_API_KEY")
    supplier_name = request.supplier_name or "Inconnu"
    product_name = request.product_name or "Inconnu"

    # Update agent configuration
    update_agent(agent_name, product_name, supplier_name)

    # Give ElevenLabs API time to propagate the configuration update
    import time

    time.sleep(1)  # Wait 2 seconds for the configuration to propagate

    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Missing ELEVENLABS_API_KEY. Please provide in request or set as environment variable.",
        )

    try:
        # Start the agent conversation asynchronously
        task_id = start_agent_async(
            agent_name=agent_name, api_key=api_key, supplier_name=supplier_name
        )

        return TaskStartResponse(
            task_id=task_id,
            agent_name=agent_name,
            supplier_name=supplier_name,
            status="pending",
            message=f"Conversation started in background. Use /api/agent/status/{task_id} to check status.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting conversation: {str(e)}",
        ) from e


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of a background conversation task.

    Args:
        task_id: The task ID returned from /start endpoint

    Returns:
        TaskStatusResponse with current task status
    """
    task = conversation_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task_dict = task.to_dict()
    return TaskStatusResponse(**task_dict)


@router.get("/tasks", response_model=List[TaskStatusResponse])
async def list_all_tasks():
    """
    List all conversation tasks.

    Returns:
        List of TaskStatusResponse with all tasks
    """
    tasks = conversation_manager.list_tasks()
    return [TaskStatusResponse(**task.to_dict()) for task in tasks]


@router.post("/parse/{task_id}")
async def parse_completed_conversation(task_id: str):
    """
    Parse a completed conversation transcript and update CSV.

    This should be called after a conversation is completed to extract
    data and update the supplier database.

    Args:
        task_id: The task ID of the completed conversation

    Returns:
        dict: Parsing result
    """
    task = conversation_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    if task.status.value != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Task {task_id} is not completed yet (status: {task.status.value})",
        )

    if not task.conversation_id:
        raise HTTPException(
            status_code=400, detail=f"Task {task_id} has no conversation_id"
        )

    # Load the transcript from file
    transcript_file = f"./data/transcripts/{task.conversation_id}.json"

    try:
        with open(transcript_file, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Transcript file not found: {transcript_file}"
        )

    # Parse the conversation
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    parser = TranscriptParserService(api_key=anthropic_api_key, data_dir="./data")

    try:
        result = parser.parse_and_update_csv(
            transcript_data, task.supplier_name, save=True
        )
        return {"status": "success", "result": result, "task_id": task_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error parsing conversation: {str(e)}"
        ) from e


def load_transcripts_from_folder(transcripts_dir: Path = TRANSCRIPTS_DIR) -> List[dict]:
    """
    Load all transcript files from the transcripts directory.

    Returns:
        List of transcript dictionaries
    """
    transcripts = []
    if not transcripts_dir.exists():
        return transcripts

    for transcript_file in transcripts_dir.glob("*.json"):
        try:
            with open(transcript_file, "r", encoding="utf-8") as f:
                transcript_data = json.load(f)
                transcripts.append(transcript_data)
        except Exception as e:
            print(f"Error loading transcript {transcript_file}: {e}")
            continue

    return transcripts


def transcript_to_activity_item(transcript: dict) -> dict:
    """
    Convert a transcript dictionary to an ActivityItem-like dictionary.

    Args:
        transcript: Transcript dictionary from JSON file

    Returns:
        Dictionary with ActivityItem structure
    """
    conversation_id = transcript.get("conversation_id", "unknown")
    supplier_name = transcript.get("supplier_name", "Unknown")
    timestamp_str = transcript.get("timestamp", "")
    total_messages = transcript.get(
        "total_messages", len(transcript.get("messages", []))
    )

    # Parse timestamp
    try:
        if timestamp_str:
            created_at = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            created_at = datetime.now()
    except Exception:
        created_at = datetime.now()

    # Infer task type from transcript content or supplier name
    messages = transcript.get("messages", [])
    message_text = " ".join([msg.get("text", "").lower() for msg in messages])

    if "delivery" in message_text or "eta" in message_text or "deliver" in message_text:
        task_type = "delivery_risk"
        description = f"Following up on delivery ETA with {supplier_name}"
    elif "price" in message_text or "pricing" in message_text or "cost" in message_text:
        task_type = "price_update"
        description = f"Updating pricing information from {supplier_name}"
    elif "product" in message_text or "new" in message_text or "offer" in message_text:
        task_type = "product_discovery"
        description = f"Searching for new products from {supplier_name}"
    else:
        task_type = "supplier_followup"
        description = f"Following up with {supplier_name}"

    # Use conversation_id as task_id for transcripts (since they don't have task_id)
    task_id = f"transcript_{conversation_id}"

    return {
        "task_id": task_id,
        "agent_name": transcript.get("agent_id", "products"),
        "supplier_name": supplier_name,
        "status": "completed",  # Transcripts are always completed
        "created_at": created_at.isoformat(),
        "started_at": created_at.isoformat(),
        "completed_at": created_at.isoformat(),
        "conversation_id": conversation_id,
        "error": None,
        "total_messages": total_messages,
        "task_type": task_type,
        "description": description,
    }


def get_all_activities() -> List[dict]:
    """
    Get all activities from both active tasks and historical transcripts.

    Returns:
        List of activity dictionaries
    """
    activities = []

    # Get active tasks from conversation manager
    tasks = conversation_manager.list_tasks()
    for task in tasks:
        agent_name_lower = task.agent_name.lower()
        if "delivery" in agent_name_lower or "eta" in agent_name_lower:
            task_type = "delivery_risk"
            description = f"Following up on delivery ETA with {task.supplier_name}"
        elif "price" in agent_name_lower or "pricing" in agent_name_lower:
            task_type = "price_update"
            description = f"Updating pricing information from {task.supplier_name}"
        elif "product" in agent_name_lower or "discovery" in agent_name_lower:
            task_type = "product_discovery"
            description = f"Searching for new products from {task.supplier_name}"
        else:
            task_type = "supplier_followup"
            description = f"Following up with {task.supplier_name}"

        task_dict = task.to_dict()
        activities.append(
            {
                **task_dict,
                "task_type": task_type,
                "description": description,
            }
        )

    # Get historical transcripts
    transcripts = load_transcripts_from_folder()
    for transcript in transcripts:
        activity = transcript_to_activity_item(transcript)
        activities.append(activity)

    return activities


@router.get("/activity/summary", response_model=ActivitySummaryResponse)
async def get_activity_summary(limit: int = 10):
    """
    Get summary statistics of agent activities.
    Counts activities from the same set shown in the recap (most recent activities).

    Args:
        limit: Maximum number of activities to count (default: 10, matches recap default)

    Returns:
        ActivitySummaryResponse with counts and time saved
    """
    # Get all activities (from both tasks and transcripts)
    all_activities = get_all_activities()

    # Sort by created_at descending (most recent first) - same as recap
    def get_created_at(activity: dict) -> datetime:
        try:
            return datetime.fromisoformat(activity["created_at"])
        except Exception:
            return datetime.min

    sorted_activities = sorted(all_activities, key=get_created_at, reverse=True)

    # Get the same activities that would be shown in recap
    recap_activities = sorted_activities[:limit]

    # Count by type (all activities in recap, regardless of status)
    delivery_risks_resolved = 0
    supplier_followups_sent = 0
    price_checks_completed = 0
    new_product_matches = 0

    for activity in recap_activities:
        task_type = activity.get("task_type", "supplier_followup")
        if task_type == "delivery_risk":
            delivery_risks_resolved += 1
        elif task_type == "price_update":
            price_checks_completed += 1
        elif task_type == "product_discovery":
            new_product_matches += 1
        else:
            supplier_followups_sent += 1

    # Estimate time saved (rough estimates based on task types)
    # Only count completed activities for time saved calculation
    completed_count = {
        "delivery_risk": 0,
        "price_update": 0,
        "product_discovery": 0,
        "supplier_followup": 0,
    }

    for activity in recap_activities:
        if activity.get("status") == "completed":
            task_type = activity.get("task_type", "supplier_followup")
            completed_count[task_type] = completed_count.get(task_type, 0) + 1

    time_saved = (
        completed_count.get("delivery_risk", 0) * 9  # ~9 min per delivery check
        + completed_count.get("supplier_followup", 0) * 6  # ~6 min per followup
        + completed_count.get("price_update", 0) * 2  # ~2 min per price check
        + completed_count.get("product_discovery", 0) * 6  # ~6 min per product search
    )

    return ActivitySummaryResponse(
        delivery_risks_resolved=delivery_risks_resolved,
        supplier_followups_sent=supplier_followups_sent,
        price_checks_completed=price_checks_completed,
        new_product_matches=new_product_matches,
        time_saved_minutes=time_saved,
    )


@router.get("/activity/recap", response_model=ActivityRecapResponse)
async def get_activity_recap(limit: int = 10):
    """
    Get recent agent activities for the daily recap.
    Includes both active tasks and historical transcripts.

    Args:
        limit: Maximum number of activities to return (default: 10)

    Returns:
        ActivityRecapResponse with list of recent activities
    """
    # Get all activities (from both tasks and transcripts)
    all_activities = get_all_activities()

    # Sort by created_at descending (most recent first)
    def get_created_at(activity: dict) -> datetime:
        try:
            return datetime.fromisoformat(activity["created_at"])
        except Exception:
            return datetime.min

    sorted_activities = sorted(all_activities, key=get_created_at, reverse=True)

    # Convert to ActivityItem and limit
    activities = []
    for activity_dict in sorted_activities[:limit]:
        activities.append(ActivityItem(**activity_dict))

    return ActivityRecapResponse(
        activities=activities,
        total_count=len(activities),
    )


@router.get("/transcript/{conversation_id}", response_model=TranscriptResponse)
async def get_transcript_by_conversation_id(conversation_id: str):
    """
    Get transcript by conversation_id.

    Args:
        conversation_id: The conversation ID

    Returns:
        TranscriptResponse with transcript data
    """
    transcript_file = Path(f"./data/transcripts/{conversation_id}.json")

    if not transcript_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Transcript not found for conversation_id: {conversation_id}",
        )

    try:
        with open(transcript_file, "r") as f:
            transcript_data = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading transcript file: {str(e)}",
        ) from e

    # Format transcript as readable text
    messages = transcript_data.get("messages", [])
    formatted_lines = []
    for msg in messages:
        role = msg.get("role", "unknown")
        text = msg.get("text", "")
        if role == "agent":
            formatted_lines.append(f"AI Agent: {text}")
        elif role == "user":
            formatted_lines.append(f"Supplier Representative: {text}")
        else:
            formatted_lines.append(f"{role.capitalize()}: {text}")

    formatted_text = "\n\n".join(formatted_lines)

    return TranscriptResponse(
        conversation_id=transcript_data.get("conversation_id", conversation_id),
        supplier_name=transcript_data.get("supplier_name", "Unknown"),
        agent_id=transcript_data.get("agent_id"),
        timestamp=transcript_data.get("timestamp", ""),
        messages=messages,
        total_messages=transcript_data.get("total_messages", len(messages)),
        formatted_text=formatted_text,
    )


@router.get("/transcript/task/{task_id}", response_model=TranscriptResponse)
async def get_transcript_by_task_id(task_id: str):
    """
    Get transcript by task_id.
    Handles both active tasks and historical transcripts.

    Args:
        task_id: The task ID (can be a real task_id or transcript_{conversation_id})

    Returns:
        TranscriptResponse with transcript data
    """
    # Check if this is a transcript-based task_id
    if task_id.startswith("transcript_"):
        conversation_id = task_id.replace("transcript_", "", 1)
        return await get_transcript_by_conversation_id(conversation_id)

    # Otherwise, try to get from active tasks
    task = conversation_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    if not task.conversation_id:
        raise HTTPException(
            status_code=400,
            detail=f"Task {task_id} has no conversation_id",
        )

    return await get_transcript_by_conversation_id(task.conversation_id)
