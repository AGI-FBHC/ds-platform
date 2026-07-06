import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class DatasetCreate(BaseModel):
    """Create a dataset (manual or from task completion)."""

    name: str
    description: str = ""
    source: str = "baidu"
    format: str = "jpg"
    fields: Dict[str, Any] = Field(default_factory=dict)
    source_task_id: Optional[str] = None
    storage_path: str = ""


class DatasetUpdate(BaseModel):
    """Update dataset fields. Partial update — only provided fields change."""

    name: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    format: Optional[str] = None
    image_count: Optional[int] = None
    total_size: Optional[int] = None
    fields: Optional[Dict[str, Any]] = None
    storage_path: Optional[str] = None
    is_published: Optional[bool] = None


class DatasetSaveFromTask(BaseModel):
    """Save a completed task as a dataset."""

    task_id: str


class DatasetImageUpdate(BaseModel):
    """Update individual image metadata."""

    filename: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    keyword: Optional[str] = None
    source_page_title: Optional[str] = None
    source_page_url: Optional[str] = None
    mask_relative_path: Optional[str] = None
    mask_status: Optional[str] = None
    labels: Optional[Dict[str, Any]] = None
    search_metadata: Optional[Dict[str, Any]] = None
    extra: Optional[Dict[str, Any]] = None


class DatasetBulkUpdate(BaseModel):
    """Bulk update datasets scoped to the current user."""

    ids: Optional[List[str]] = None
    where: Optional[Dict[str, Any]] = None
    set: Optional[Dict[str, Any]] = None
    remove: Optional[List[str]] = None
    limit: int = 1000
    dry_run: bool = False

    @field_validator("limit")
    @classmethod
    def _check_limit(cls, value: int) -> int:
        if value < 1 or value > 10000:
            raise ValueError("limit must be between 1 and 10000")
        return value

    @field_validator("set", "remove", "where")
    @classmethod
    def _check_paths(cls, value):
        if value is None:
            return value
        items = value.keys() if isinstance(value, dict) else value
        for item in items:
            if not isinstance(item, str):
                continue
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.\$(\.[a-zA-Z_][a-zA-Z0-9_]*)+)?$", item):
                raise ValueError(f"invalid path: {item}")
        return value


class DatasetImageBulkUpdate(BaseModel):
    """Bulk update dataset image metadata scoped to one dataset."""

    image_ids: Optional[List[str]] = None
    where: Optional[Dict[str, Any]] = None
    set: Optional[Dict[str, Any]] = None
    remove: Optional[List[str]] = None
    limit: int = 1000
    dry_run: bool = False

    @field_validator("limit")
    @classmethod
    def _check_image_limit(cls, value: int) -> int:
        if value < 1 or value > 10000:
            raise ValueError("limit must be between 1 and 10000")
        return value

    @field_validator("set", "remove", "where")
    @classmethod
    def _check_image_paths(cls, value):
        if value is None:
            return value
        items = value.keys() if isinstance(value, dict) else value
        for item in items:
            if not isinstance(item, str):
                continue
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.\$(\.[a-zA-Z_][a-zA-Z0-9_]*)+)?$", item):
                raise ValueError(f"invalid path: {item}")
        return value


class DatasetImageResponse(BaseModel):
    id: str
    dataset_id: str
    filename: str
    relative_path: str
    url: str
    width: int
    height: int
    file_size: int
    keyword: str
    sort_order: int
    source_page_title: str = ""
    source_page_url: str = ""
    mask_relative_path: str = ""
    mask_status: str = "not_requested"
    labels: Dict[str, Any] = Field(default_factory=dict)
    search_metadata: Dict[str, Any] = Field(default_factory=dict)
    extra: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("labels", "search_metadata", "extra", mode="before")
    @classmethod
    def _none_to_empty_dict(cls, value):
        """JSON columns may be NULL in DB; coerce to {} so pydantic strict mode accepts them."""
        return value if value is not None else {}

    class Config:
        from_attributes = True


class DatasetResponse(BaseModel):
    id: str
    name: str
    description: str
    source: str
    format: str
    image_count: int
    total_size: int
    fields: Dict[str, Any]
    source_task_id: Optional[str] = None
    user_id: str
    storage_path: str
    is_published: bool = False
    published_at: Optional[datetime] = None
    owner_nickname: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    images: List[DatasetImageResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class DatasetListItem(BaseModel):
    """Lighter response for listing (no images)."""

    id: str
    name: str
    description: str
    source: str
    format: str
    image_count: int
    total_size: int
    fields: Dict[str, Any]
    source_task_id: Optional[str] = None
    user_id: str
    storage_path: str
    is_published: bool = False
    published_at: Optional[datetime] = None
    owner_nickname: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
