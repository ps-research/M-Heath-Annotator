"""
Data API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.responses import APIResponse
from backend.services.data_service import DataService

router = APIRouter()
data_service = DataService()


@router.get("/annotations")
async def get_annotations(
    annotator_ids: Optional[List[int]] = Query(None),
    domains: Optional[List[str]] = Query(None),
    malformed_only: bool = Query(False),
    completed_only: bool = Query(False),
    search_text: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=10, le=500)
):
    """Get paginated list of annotations with filters."""
    try:
        filters = {
            "page": page,
            "page_size": page_size,
            "malformed_only": malformed_only,
            "completed_only": completed_only
        }
        
        if annotator_ids:
            filters["annotator_ids"] = annotator_ids
        if domains:
            filters["domains"] = domains
        if search_text:
            filters["search_text"] = search_text
        
        result = data_service.get_annotations(filters)
        return APIResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/annotations/{annotator_id}/{domain}")
async def get_worker_annotations(
    annotator_id: int,
    domain: str,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all annotations for a specific worker (annotator-domain pair)."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")

    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain")

    try:
        annotations = data_service.get_worker_annotations(annotator_id, domain, limit)
        return APIResponse(success=True, data=annotations)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/annotations/{annotator_id}/{domain}/{sample_id}")
async def get_annotation(annotator_id: int, domain: str, sample_id: str):
    """Get specific annotation detail."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")

    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain")

    try:
        annotation = data_service.get_annotation(annotator_id, domain, sample_id)
        return APIResponse(success=True, data=annotation)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(
    annotator_ids: Optional[List[int]] = Query(None),
    domains: Optional[List[str]] = Query(None)
):
    """Get aggregated statistics across all data."""
    try:
        filters = {}
        if annotator_ids:
            filters["annotator_ids"] = annotator_ids
        if domains:
            filters["domains"] = domains
        
        stats = data_service.get_statistics(filters)
        return APIResponse(success=True, data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry/{annotator_id}/{domain}/{sample_id}")
async def retry_annotation(annotator_id: int, domain: str, sample_id: str):
    """Re-annotate a malformed sample."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")
    
    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain")
    
    try:
        # For now, return not implemented
        return APIResponse(
            success=False,
            data={},
            message="Retry functionality not yet implemented in Phase 2"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
