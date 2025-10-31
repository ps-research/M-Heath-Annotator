"""
API response models for the FastAPI backend.
"""

from typing import Generic, TypeVar, List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """Generic success response wrapper."""
    success: bool = True
    data: T
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WorkerStatusResponse(BaseModel):
    """Status of a single worker."""
    annotator_id: int
    domain: str
    status: str  # not_started, running, paused, stopped, completed, crashed
    running: bool
    stale: bool
    enabled: bool
    progress: Dict[str, Any]
    last_updated: str
    pid: Optional[int] = None


class SystemOverview(BaseModel):
    """High-level system statistics."""
    total_workers: int = 30
    enabled_workers: int
    running_workers: int
    paused_workers: int
    completed_workers: int
    crashed_workers: int
    total_progress: Dict[str, Any]
    avg_speed: float
    estimated_time_remaining: Optional[str] = None


class AnnotationRecord(BaseModel):
    """Single annotation with metadata."""
    annotator_id: int
    domain: str
    id: str
    text: str
    response: str
    label: str
    malformed: bool
    parsing_error: Optional[str] = None
    validity_error: Optional[str] = None
    timestamp: str


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PromptMetadata(BaseModel):
    """Metadata about a prompt."""
    length: int
    last_modified: str
    is_override: bool = False


class PromptDetail(BaseModel):
    """Detailed prompt information."""
    content: str
    is_override: bool
    source_path: str
    last_modified: str


class WorkerControlResult(BaseModel):
    """Result of a worker control operation."""
    annotator: int
    domain: str
    status: str
    pid: Optional[int] = None
    message: Optional[str] = None


class ResetResult(BaseModel):
    """Result of reset operation."""
    deleted_workers: int
    deleted_samples: int
    deleted_files: List[str]


class HealthReport(BaseModel):
    """System health report."""
    crashed: List[Dict[str, Any]]
    stalled: List[Dict[str, Any]]
    healthy: int


class QuotaStatus(BaseModel):
    """API quota usage estimate."""
    requests_today: int
    quota_limit: int = 1500
    percentage_used: float
    estimated_depletion: Optional[str] = None


class StatisticsReport(BaseModel):
    """Aggregated statistics."""
    total_annotations: int
    malformed_count: int
    malformed_percentage: float
    by_domain: Dict[str, Dict[str, int]]
    by_annotator: Dict[str, Dict[str, int]]
    label_distribution: Dict[str, Dict[str, int]]
