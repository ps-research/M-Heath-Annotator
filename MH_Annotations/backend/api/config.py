"""
Configuration API endpoints.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.schemas import (
    ConfigUpdate, APIKeyUpdate, AnnotatorDomainConfig, PromptUpdate,
    PromptVersionCreate, ActiveVersionUpdate
)
from backend.models.responses import APIResponse
from backend.services.config_service import ConfigService

router = APIRouter()
config_service = ConfigService()


@router.get("/settings")
async def get_settings():
    """Get current system settings."""
    try:
        settings = config_service.get_settings()
        return APIResponse(success=True, data=settings, message="Settings retrieved successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings")
async def update_settings(updates: ConfigUpdate):
    """Update system settings."""
    try:
        update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
        if not update_dict:
            raise HTTPException(status_code=400, detail="At least one field must be provided")
        
        updated_settings = config_service.update_settings(update_dict)
        return APIResponse(
            success=True,
            data=updated_settings,
            message="Settings updated successfully. Restart workers for changes to take effect."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api-keys")
async def get_api_keys():
    """Get all API keys (masked)."""
    try:
        keys = config_service.get_api_keys(masked=True)
        return APIResponse(success=True, data=keys, message="API keys retrieved successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api-keys/{annotator_id}")
async def update_api_key(annotator_id: int, key_update: APIKeyUpdate):
    """Update API key for specific annotator."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")
    
    try:
        config_service.update_api_key(annotator_id, key_update.api_key)
        return APIResponse(
            success=True,
            data={"annotator_id": annotator_id},
            message=f"API key updated for annotator {annotator_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/annotators/{annotator_id}/domains/{domain}")
async def get_domain_config(annotator_id: int, domain: str):
    """Get configuration for specific annotator-domain pair."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")
    
    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Must be one of: {', '.join(valid_domains)}")
    
    try:
        config = config_service.get_domain_config(annotator_id, domain)
        return APIResponse(success=True, data=config)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/annotators/{annotator_id}/domains/{domain}")
async def update_domain_config(annotator_id: int, domain: str, config: AnnotatorDomainConfig):
    """Update configuration for specific annotator-domain pair."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")
    
    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Must be one of: {', '.join(valid_domains)}")
    
    try:
        config_dict = {k: v for k, v in config.model_dump().items() if v is not None}
        if not config_dict:
            raise HTTPException(status_code=400, detail="At least one field must be provided")
        
        config_service.update_domain_config(annotator_id, domain, config_dict)
        return APIResponse(
            success=True,
            data={"annotator_id": annotator_id, "domain": domain},
            message="Configuration updated. Restart worker for changes to take effect."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts")
async def list_prompts():
    """List all prompts (base + overrides) with metadata."""
    try:
        prompts = config_service.list_prompts()
        return APIResponse(success=True, data=prompts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/{annotator_id}/{domain}")
async def get_prompt(annotator_id: int, domain: str):
    """Get prompt content for specific annotator-domain."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")
    
    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Must be one of: {', '.join(valid_domains)}")
    
    try:
        prompt = config_service.get_prompt(annotator_id, domain)
        return APIResponse(success=True, data=prompt)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/prompts/{annotator_id}/{domain}")
async def update_prompt(annotator_id: int, domain: str, prompt: PromptUpdate):
    """Create/update prompt override."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")
    
    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Must be one of: {', '.join(valid_domains)}")
    
    try:
        config_service.save_prompt_override(annotator_id, domain, prompt.content)
        return APIResponse(
            success=True,
            data={"annotator_id": annotator_id, "domain": domain},
            message="Prompt override saved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/prompts/{annotator_id}/{domain}")
async def delete_prompt(annotator_id: int, domain: str):
    """Delete prompt override (revert to base)."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")

    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Must be one of: {', '.join(valid_domains)}")

    try:
        config_service.delete_prompt_override(annotator_id, domain)
        return APIResponse(
            success=True,
            data={"annotator_id": annotator_id, "domain": domain},
            message="Prompt override deleted. Will now use base prompt."
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===========================
# Phase 3 - Version Management Endpoints
# ===========================

@router.post("/prompts/{annotator_id}/{domain}/versions")
async def save_prompt_version(annotator_id: int, domain: str, version_data: PromptVersionCreate):
    """Save a new prompt version."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")

    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Must be one of: {', '.join(valid_domains)}")

    try:
        result = config_service.save_prompt_version(
            annotator_id,
            domain,
            version_data.version_name,
            version_data.content,
            version_data.description
        )
        return APIResponse(
            success=True,
            data=result,
            message="Prompt version saved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/{annotator_id}/{domain}/versions")
async def list_prompt_versions(annotator_id: int, domain: str):
    """List all prompt versions for annotator-domain."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")

    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Must be one of: {', '.join(valid_domains)}")

    try:
        versions = config_service.list_prompt_versions(annotator_id, domain)
        return APIResponse(success=True, data=versions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/prompts/{annotator_id}/{domain}/active-version")
async def set_active_version(annotator_id: int, domain: str, update: ActiveVersionUpdate):
    """Set the active prompt version for annotator-domain."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")

    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Must be one of: {', '.join(valid_domains)}")

    try:
        result = config_service.set_active_version(annotator_id, domain, update.filename)
        return APIResponse(
            success=True,
            data=result,
            message="Active version updated successfully"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/prompts/{annotator_id}/{domain}/versions/{filename}")
async def delete_prompt_version(annotator_id: int, domain: str, filename: str):
    """Delete a specific prompt version."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")

    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Must be one of: {', '.join(valid_domains)}")

    try:
        config_service.delete_prompt_version(annotator_id, domain, filename)
        return APIResponse(
            success=True,
            data={"annotator_id": annotator_id, "domain": domain, "filename": filename},
            message="Version deleted successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/{annotator_id}/{domain}/versions/{filename}")
async def get_version_content(annotator_id: int, domain: str, filename: str):
    """Get full content of a specific prompt version."""
    if annotator_id < 1 or annotator_id > 5:
        raise HTTPException(status_code=400, detail="Annotator ID must be between 1 and 5")

    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if domain not in valid_domains:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Must be one of: {', '.join(valid_domains)}")

    try:
        version_content = config_service.get_version_content(annotator_id, domain, filename)
        return APIResponse(success=True, data=version_content)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
