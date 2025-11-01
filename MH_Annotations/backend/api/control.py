"""
Control API endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.schemas import WorkerControlRequest, ResetRequest
from backend.models.responses import APIResponse
from backend.services.worker_service import WorkerService
from backend.services.run_service import RunService

router = APIRouter()
worker_service = WorkerService()
run_service = RunService()


@router.post("/start")
async def start_workers(request: WorkerControlRequest = None):
    """Start worker(s)."""
    try:
        filters = {}
        if request:
            if request.annotator_id:
                filters["annotator_id"] = request.annotator_id
            if request.domain:
                filters["domain"] = request.domain
        
        results = worker_service.start_workers(filters)
        return APIResponse(success=True, data=results, message="Start command executed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_workers(request: WorkerControlRequest = None):
    """Stop worker(s)."""
    try:
        filters = {}
        if request:
            if request.annotator_id:
                filters["annotator_id"] = request.annotator_id
            if request.domain:
                filters["domain"] = request.domain
        
        results = worker_service.stop_workers(filters, timeout=30)
        return APIResponse(success=True, data=results, message="Stop command executed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pause")
async def pause_workers(request: WorkerControlRequest = None):
    """Pause worker(s)."""
    try:
        filters = {}
        if request:
            if request.annotator_id:
                filters["annotator_id"] = request.annotator_id
            if request.domain:
                filters["domain"] = request.domain
        
        results = worker_service.pause_workers(filters)
        return APIResponse(success=True, data=results, message="Pause signal sent")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume")
async def resume_workers(request: WorkerControlRequest = None):
    """Resume worker(s)."""
    try:
        filters = {}
        if request:
            if request.annotator_id:
                filters["annotator_id"] = request.annotator_id
            if request.domain:
                filters["domain"] = request.domain
        
        results = worker_service.resume_workers(filters)
        return APIResponse(success=True, data=results, message="Resume signal sent")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_data(request: ResetRequest):
    """Reset annotation data. DESTRUCTIVE OPERATION."""
    try:
        # Confirmation already validated by Pydantic model
        result = worker_service.reset_data(
            scope=request.scope,
            annotator_id=request.annotator_id,
            domain=request.domain
        )
        return APIResponse(
            success=True,
            data=result,
            message="Data reset completed"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart/{annotator_id}/{domain}")
async def restart_worker(annotator_id: int, domain: str):
    """Restart specific worker from last checkpoint."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")

    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain")

    try:
        # Stop first
        stop_result = worker_service.stop_workers({"annotator_id": annotator_id, "domain": domain}, timeout=30)

        # Start again
        start_result = worker_service.start_workers({"annotator_id": annotator_id, "domain": domain})

        return APIResponse(
            success=True,
            data={"stop": stop_result, "start": start_result},
            message=f"Worker restarted for annotator {annotator_id}, domain {domain}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enabled-workers")
async def get_enabled_workers():
    """Get all enabled workers with their full configuration."""
    try:
        workers = run_service.get_enabled_workers()
        return APIResponse(
            success=True,
            data=workers,
            message=f"Found {len(workers)} enabled workers"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/annotator-summaries")
async def get_annotator_summaries():
    """Get configuration summaries for all annotators with enabled domains."""
    try:
        summaries = run_service.get_all_annotator_summaries()
        return APIResponse(
            success=True,
            data=summaries,
            message=f"Found {len(summaries)} annotators with enabled domains"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/annotator-summaries/{annotator_id}")
async def get_annotator_summary(annotator_id: int):
    """Get configuration summary for specific annotator."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")

    try:
        summary = run_service.get_annotator_summary(annotator_id)
        return APIResponse(success=True, data=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/factory-reset")
async def factory_reset(confirmation: str):
    """Factory reset - deletes ALL data including annotations, progress, logs, and control files. DESTRUCTIVE!"""
    if confirmation != "FACTORY_RESET":
        raise HTTPException(
            status_code=400,
            detail="Confirmation must equal 'FACTORY_RESET' exactly"
        )

    try:
        # First stop all workers
        worker_service.stop_workers({}, timeout=30)

        # Then perform complete data deletion
        result = worker_service.reset_data(scope="all")

        return APIResponse(
            success=True,
            data=result,
            message="Factory reset completed - all data has been deleted"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
