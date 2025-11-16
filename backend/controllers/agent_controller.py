"""Controller for ElevenLabs agent service endpoints."""

import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from backend.services.conversation_manager import conversation_manager
from backend.services.elevenlabs_agent_service import start_agent_async
from backend.services.transcript_parser_service import TranscriptParserService

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
    # update_agent(product_name, supplier_name)
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
    import json

    transcript_file = f"./data/transcripts/{task.conversation_id}.json"

    try:
        with open(transcript_file, "r") as f:
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
