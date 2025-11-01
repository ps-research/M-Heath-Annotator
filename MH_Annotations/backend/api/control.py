"""
Control API endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.schemas import (
    WorkerControlRequest,
    ResetRequest,
    RunStartRequest,
    FactoryResetRequest
)
from backend.models.responses import APIResponse
from backend.services.worker_service import WorkerService

router = APIRouter()
worker_service = WorkerService()


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


# ===========================
# Run Management Endpoints
# ===========================

@router.post("/run/validate")
async def validate_run_start():
    """
    Validate that a run can be started.

    Checks:
    - At least one worker is enabled
    - All enabled workers have API keys
    - All enabled workers have prompts
    - Dataset file exists and is readable

    Returns validation result with errors/warnings.
    """
    try:
        result = worker_service.validate_run_start()
        return APIResponse(
            success=result["valid"],
            data=result,
            message="Validation complete" if result["valid"] else "Validation failed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/start")
async def start_run(request: RunStartRequest = None):
    """
    Start a new run.

    If validate_only is True, only validates without starting.
    Otherwise, validates and starts all enabled workers.
    """
    try:
        # Always validate first
        validation = worker_service.validate_run_start()

        if not validation["valid"]:
            return APIResponse(
                success=False,
                data=validation,
                message="Cannot start run: validation failed"
            )

        # If validate_only, return validation result
        if request and request.validate_only:
            return APIResponse(
                success=True,
                data=validation,
                message="Validation successful"
            )

        # Start all enabled workers
        results = worker_service.start_workers({})

        return APIResponse(
            success=True,
            data={
                "validation": validation,
                "start_results": results
            },
            message=f"Run started: {len(validation['enabled_workers'])} workers"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset/current-run")
async def reset_current_run():
    """
    Reset current run data.

    Stops all workers and deletes:
    - All annotations
    - All progress logs
    - All control files

    This is a DESTRUCTIVE operation.
    """
    try:
        # Stop all workers first
        worker_service.stop_workers({}, timeout=30)

        # Delete all data
        result = worker_service.reset_data(scope="all")

        return APIResponse(
            success=True,
            data=result,
            message="Current run data deleted"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset/factory")
async def factory_reset(request: FactoryResetRequest):
    """
    Factory reset - DELETE EVERYTHING.

    This is the nuclear option. Deletes:
    - All annotations from all runs
    - All progress logs
    - All control files
    - All exported data
    - Everything in data directory except source

    This CANNOT be undone.
    """
    try:
        # Confirmation already validated by Pydantic

        # Stop all workers first
        worker_service.stop_workers({}, timeout=30)

        # Perform factory reset
        result = worker_service.factory_reset()

        return APIResponse(
            success=True,
            data=result,
            message="Factory reset complete - all data deleted"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers/grid-status")
async def get_workers_grid_status():
    """
    Get status of all enabled workers in format suitable for grid display.

    Only returns enabled workers with enhanced status information.
    """
    try:
        workers = worker_service.get_grid_status()
        return APIResponse(
            success=True,
            data=workers,
            message=f"Retrieved status for {len(workers)} workers"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
