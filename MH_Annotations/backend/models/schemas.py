"""
Data models and schemas for the annotation system.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ProgressStats(BaseModel):
    """Statistics for annotation progress."""
    total_completed: int = 0
    malformed_count: int = 0
    start_time: Optional[str] = None
    last_speed_check: Optional[str] = None
    samples_per_min: float = 0.0


class Progress(BaseModel):
    """Progress tracking for annotator-domain pair."""
    annotator_id: int
    domain: str
    enabled: bool = True
    target_count: int = 0
    status: str = "not_started"  # not_started, running, paused, stopped, completed, crashed
    completed_ids: List[str] = Field(default_factory=list)
    malformed_ids: List[str] = Field(default_factory=list)
    last_processed_id: Optional[str] = None
    last_updated: str
    pid: Optional[int] = None
    stats: ProgressStats = Field(default_factory=ProgressStats)

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ["not_started", "running", "paused", "stopped", "completed", "crashed"]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}")
        return v


class AnnotationResult(BaseModel):
    """Result of annotating a single sample."""
    id: str
    text: str
    response: str
    label: str
    malformed: bool
    parsing_error: Optional[str] = None
    validity_error: Optional[str] = None
    timestamp: str


class ControlSignal(BaseModel):
    """Control signal for worker process."""
    command: str  # pause, resume, stop
    timestamp: str

    @field_validator('command')
    @classmethod
    def validate_command(cls, v):
        valid_commands = ["pause", "resume", "stop"]
        if v not in valid_commands:
            raise ValueError(f"Invalid command: {v}")
        return v


class WorkerStatus(BaseModel):
    """Status information for a worker."""
    annotator_id: int
    domain: str
    status: str
    running: bool
    stale: bool
    progress: Dict[str, Any]
    last_updated: str


class GlobalSettings(BaseModel):
    """Global configuration settings."""
    model_name: str = "gemini-2.0-flash-exp"
    request_delay_seconds: int = 1
    max_retries: int = 3
    crash_detection_minutes: int = 5
    control_check_iterations: int = 5
    control_check_seconds: int = 10


class DomainConfig(BaseModel):
    """Configuration for annotator-domain pair."""
    enabled: bool = False
    target_count: int = 0


class Settings(BaseModel):
    """Complete settings configuration."""
    global_config: GlobalSettings = Field(alias="global")
    annotators: Dict[str, Dict[str, DomainConfig]]

    class Config:
        populate_by_name = True


# ===========================
# Phase 2 API Schemas
# ===========================

class ConfigUpdate(BaseModel):
    """Request to update global settings."""
    model_name: Optional[str] = None
    request_delay_seconds: Optional[int] = Field(None, ge=0, le=10)
    max_retries: Optional[int] = Field(None, ge=1, le=10)
    crash_detection_minutes: Optional[int] = Field(None, ge=1, le=30)
    control_check_iterations: Optional[int] = Field(None, ge=1, le=20)
    control_check_seconds: Optional[int] = Field(None, ge=1, le=60)

    @field_validator('model_name', 'request_delay_seconds', 'max_retries',
                     'crash_detection_minutes', 'control_check_iterations',
                     'control_check_seconds')
    @classmethod
    def check_at_least_one(cls, v, info):
        """Ensure at least one field is provided."""
        # This will be checked at the model level
        return v


class APIKeyUpdate(BaseModel):
    """Request to update API key."""
    api_key: Optional[str] = Field(None)  # Allow None for deletion
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        # If provided and not None, must be at least 20 chars
        if v is not None and len(v) < 20:
            raise ValueError('API key must be at least 20 characters')
        return v


class AnnotatorDomainConfig(BaseModel):
    """Configuration for specific annotator-domain pair."""
    enabled: Optional[bool] = None
    target_count: Optional[int] = Field(None, ge=0, le=2000)


class WorkerControlRequest(BaseModel):
    """Request to control worker operations."""
    annotator_id: Optional[int] = Field(None, ge=1, le=5)
    domain: Optional[str] = None
    action: str = Field(..., pattern="^(start|stop|pause|resume)$")

    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v):
        if v is not None:
            valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
            if v not in valid_domains:
                raise ValueError(f"Invalid domain: {v}")
        return v


class ResetRequest(BaseModel):
    """Request to reset annotation data."""
    scope: str = Field(..., pattern="^(single|all)$")
    annotator_id: Optional[int] = Field(None, ge=1, le=5)
    domain: Optional[str] = None
    confirmation: str = Field(..., min_length=1)

    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v):
        if v is not None:
            valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
            if v not in valid_domains:
                raise ValueError(f"Invalid domain: {v}")
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate that single scope has required fields."""
        if self.scope == "single":
            if self.annotator_id is None or self.domain is None:
                raise ValueError("annotator_id and domain are required when scope is 'single'")
        if self.confirmation != "DELETE":
            raise ValueError("confirmation must equal 'DELETE' exactly")


class PromptUpdate(BaseModel):
    """Request to update prompt."""
    content: str = Field(..., min_length=100)

    @field_validator('content')
    @classmethod
    def validate_placeholder(cls, v):
        if "{text}" not in v:
            raise ValueError("Prompt must contain {text} placeholder")
        return v


class DataFilter(BaseModel):
    """Filter for querying annotations."""
    annotator_ids: List[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])
    domains: List[str] = Field(default_factory=lambda: ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"])
    malformed_only: bool = False
    completed_only: bool = False
    search_text: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=10, le=500)


class ExportRequest(BaseModel):
    """Request to export annotations."""
    format: str = Field(..., pattern="^(excel|json)$")
    filters: DataFilter = Field(default_factory=DataFilter)
    include_columns: List[str] = Field(default_factory=lambda: ["all"])
    excel_options: Optional[Dict[str, bool]] = Field(default_factory=lambda: {
        "multi_sheet": True,
        "include_summary": True
    })


# ===========================
# Phase 3 - Version Management Schemas
# ===========================

class PromptVersionCreate(BaseModel):
    """Request to create a new prompt version."""
    version_name: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=100)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator('version_name')
    @classmethod
    def validate_version_name(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Version name must contain only letters, numbers, and underscores')
        return v

    @field_validator('content')
    @classmethod
    def validate_placeholder(cls, v):
        if '{text}' not in v:
            raise ValueError('Prompt must contain {text} placeholder')
        return v


class ActiveVersionUpdate(BaseModel):
    """Request to set active version."""
    filename: Optional[str] = None  # Can be None to revert to base

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        if v is not None:
            if not v.startswith('v') or not v.endswith('.txt'):
                raise ValueError('Invalid filename format')
        return v
