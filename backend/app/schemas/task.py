from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Create task - fields will be filled via agent chat."""

    agent_type: str = "image_crawler"
    initial_config: Optional[Dict[str, Any]] = None


class TaskConfig(BaseModel):
    """Image crawler agent configuration."""

    subject: str = ""
    keywords: List[str] = Field(default_factory=list)
    classification_axes: List[Dict[str, Any]] = Field(default_factory=list)
    search_items: List[Dict[str, Any]] = Field(default_factory=list)
    max_count: int = 100
    format: str = "jpg"
    min_width: Optional[int] = None
    min_height: Optional[int] = None
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    need_mask: bool = False
    mask_provider: Optional[str] = None


class AgentMessage(BaseModel):
    """Single message in agent chat."""

    role: str
    content: str
    timestamp: Optional[datetime] = None


class AgentChatRequest(BaseModel):
    """Request to chat with agent."""

    task_id: str
    message: str


class AgentChatResponse(BaseModel):
    """Agent response."""

    message: str
    is_complete: bool = False
    config_summary: Optional[Dict[str, Any]] = None
    missing_fields: List[str] = Field(default_factory=list)


class TaskRename(BaseModel):
    """Patch a task. Both fields optional; only provided ones are updated."""

    name: Optional[str] = None
    task_config: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    id: str
    name: str
    status: str
    progress: int
    message: str
    task_config: Optional[Dict[str, Any]] = None
    chat_history: Optional[List[Dict[str, Any]]] = None
    agent_type: Optional[str] = None
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskProgress(BaseModel):
    task_id: str
    status: str
    progress: int
    message: str
