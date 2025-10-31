"""
Monitoring API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.responses import APIResponse
from backend.services.monitoring_service import MonitoringService

router = APIRouter()
monitoring_service = MonitoringService()


@router.get("/overview")
async def get_overview():
    """Get system-wide statistics."""
    try:
        overview = monitoring_service.get_system_overview()
        return APIResponse(success=True, data=overview)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers")
async def get_workers(
    annotator_id: Optional[int] = Query(None, ge=1, le=5),
    domain: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get status of all workers with optional filters."""
    try:
        filters = {}
        if annotator_id:
            filters["annotator_id"] = annotator_id
        if domain:
            valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
            if domain not in valid_domains:
                raise HTTPException(status_code=400, detail=f"Invalid domain")
            filters["domain"] = domain
        if status:
            valid_statuses = ["not_started", "running", "paused", "stopped", "completed", "crashed"]
            if status not in valid_statuses:
                raise HTTPException(status_code=400, detail=f"Invalid status")
            filters["status"] = status
        
        workers = monitoring_service.get_all_worker_statuses(filters)
        return APIResponse(success=True, data=workers)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers/{annotator_id}/{domain}")
async def get_worker(annotator_id: int, domain: str):
    """Get detailed status of specific worker."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")
    
    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain")
    
    try:
        worker = monitoring_service.get_worker_status(annotator_id, domain)
        return APIResponse(success=True, data=worker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def check_health():
    """Detect crashed/stalled workers."""
    try:
        health = monitoring_service.check_health()
        return APIResponse(success=True, data=health)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quota")
async def get_quota():
    """Get API quota usage estimates."""
    try:
        quota = monitoring_service.get_quota_status()
        return APIResponse(success=True, data=quota)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_logs(
    level: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    annotator_id: Optional[int] = Query(None, ge=1, le=5),
    domain: Optional[str] = Query(None)
):
    """Get recent system logs."""
    try:
        # For now, return empty logs - would need to implement log reading
        logs = []
        return APIResponse(success=True, data=logs, message="Log reading not yet implemented")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
