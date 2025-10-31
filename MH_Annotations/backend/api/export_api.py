"""
Export API endpoints.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.schemas import ExportRequest
from backend.models.responses import APIResponse
from backend.services.export_service import ExportService

router = APIRouter()
export_service = ExportService()


@router.post("")
async def export_data(request: ExportRequest):
    """Export annotations in specified format."""
    try:
        # Generate export file
        file_path = export_service.generate_export(request.model_dump())
        
        # Determine media type and filename
        if request.format == "json":
            media_type = "application/json"
            filename = f"annotations_export_{request.filters.page}.json"
        elif request.format == "excel":
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = "annotations_export.xlsx"
        else:
            raise HTTPException(status_code=400, detail="Invalid export format")
        
        # Return file
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview")
async def preview_export(
    format: str = "json",
    annotator_ids: str = "1,2,3,4,5",
    domains: str = "all"
):
    """Preview export (first 10 rows) without generating full file."""
    try:
        # Parse parameters
        ann_ids = [int(x) for x in annotator_ids.split(",")]
        dom_list = domains.split(",") if domains != "all" else ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
        
        # Create filter
        filters = {
            "annotator_ids": ann_ids,
            "domains": dom_list,
            "page_size": 10,
            "page": 1
        }
        
        # Get preview data
        from backend.services.data_service import DataService
        data_service = DataService()
        result = data_service.get_annotations(filters)
        
        return APIResponse(
            success=True,
            data={
                "preview": result["items"],
                "total_records": result["total"],
                "format": format
            },
            message="Export preview generated"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
