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
