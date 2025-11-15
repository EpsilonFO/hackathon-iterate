"""Manager for tracking background conversation tasks."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class ConversationStatus(str, Enum):
    """Status of a conversation task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ConversationTask:
    """Represents a background conversation task."""

    def __init__(
        self,
        task_id: str,
        agent_name: str,
        supplier_name: str,
    ):
        self.task_id = task_id
        self.agent_name = agent_name
        self.supplier_name = supplier_name
        self.status = ConversationStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.conversation_id: Optional[str] = None
        self.error: Optional[str] = None
        self.total_messages: int = 0

    def to_dict(self) -> dict:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "supplier_name": self.supplier_name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "conversation_id": self.conversation_id,
            "error": self.error,
            "total_messages": self.total_messages,
        }


class ConversationManager:
    """Manages background conversation tasks."""

    def __init__(self):
        self._tasks: Dict[str, ConversationTask] = {}

    def create_task(self, agent_name: str, supplier_name: str) -> ConversationTask:
        """Create a new conversation task."""
        task_id = str(uuid.uuid4())
        task = ConversationTask(
            task_id=task_id,
            agent_name=agent_name,
            supplier_name=supplier_name,
        )
        self._tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[ConversationTask]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def update_task_status(
        self,
        task_id: str,
        status: ConversationStatus,
        conversation_id: Optional[str] = None,
        error: Optional[str] = None,
        total_messages: int = 0,
    ):
        """Update task status."""
        task = self._tasks.get(task_id)
        if task:
            task.status = status
            if status == ConversationStatus.RUNNING and not task.started_at:
                task.started_at = datetime.now()
            elif status in [ConversationStatus.COMPLETED, ConversationStatus.FAILED]:
                task.completed_at = datetime.now()
            if conversation_id:
                task.conversation_id = conversation_id
            if error:
                task.error = error
            if total_messages:
                task.total_messages = total_messages

    def list_tasks(self) -> list[ConversationTask]:
        """List all tasks."""
        return list(self._tasks.values())


# Global manager instance
conversation_manager = ConversationManager()
