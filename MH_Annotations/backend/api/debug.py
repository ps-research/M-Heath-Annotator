"""
Debug API endpoints for testing and diagnostics.

NEW: Provides endpoints to test Gemini API communication and system health.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.annotator import GeminiAnnotator
from backend.core.parser import ResponseParser
from backend.core.process_registry import ProcessRegistry
from backend.models.responses import APIResponse
from backend.utils.file_operations import atomic_read_json

router = APIRouter()


class TestGeminiRequest(BaseModel):
    """Request model for testing Gemini API."""
    annotator_id: int
    domain: str
    sample_text: str


@router.post("/test-gemini")
async def test_gemini_api(request: TestGeminiRequest):
    """
    Test Gemini API with a sample text.

    Returns full request and response for debugging.
    This is useful for manually verifying that workers can communicate with Gemini.

    Args:
        request: Contains annotator_id, domain, and sample_text

    Returns:
        Full request details (prompt, model) and response details (raw response, parsed label, errors)
    """
    try:
        base_dir = Path(__file__).parent.parent.parent

        # Validate annotator_id
        if request.annotator_id < 1 or request.annotator_id > 5:
            raise HTTPException(400, "Annotator ID must be between 1 and 5")

        # Validate domain
        valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
        if request.domain not in valid_domains:
            raise HTTPException(400, f"Invalid domain. Must be one of: {valid_domains}")

        # Load API key
        api_keys_path = base_dir / "config" / "api_keys.json"
        api_keys = atomic_read_json(str(api_keys_path))

        if not api_keys:
            raise HTTPException(500, "API keys file not found")

        api_key = api_keys.get(f"annotator_{request.annotator_id}")
        if not api_key:
            raise HTTPException(400, f"API key not found for annotator {request.annotator_id}")

        # Load prompt template
        # Check for override first
        override_path = base_dir / "config" / "prompts" / "overrides" / f"annotator_{request.annotator_id}" / f"{request.domain}.txt"
        base_prompt_path = base_dir / "config" / "prompts" / "base" / f"{request.domain}.txt"

        if override_path.exists():
            prompt_path = override_path
            prompt_source = "override"
        elif base_prompt_path.exists():
            prompt_path = base_prompt_path
            prompt_source = "base"
        else:
            raise HTTPException(404, f"Prompt template not found for domain: {request.domain}")

        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        # Format prompt
        try:
            prompt = prompt_template.format(text=request.sample_text)
        except KeyError as e:
            raise HTTPException(400, f"Prompt template missing placeholder: {e}")

        # Load model name from settings
        settings = atomic_read_json(str(base_dir / "config" / "settings.json"))
        if not settings:
            raise HTTPException(500, "Settings file not found")

        model_name = settings.get("global", {}).get("model_name", "gemini-2.0-flash-exp")

        # Call Gemini API
        print(f"\n🧪 Testing Gemini API for Annotator {request.annotator_id}, Domain {request.domain}")
        print(f"   Sample text: {request.sample_text[:100]}...")

        gemini = GeminiAnnotator(api_key, model_name)
        response_text, error = gemini.generate(prompt)

        # Parse response
        parser = ResponseParser()
        label = None
        parsing_error = None
        validity_error = None

        if response_text:
            label, parsing_error, validity_error = parser.parse_response(
                response_text,
                request.domain
            )

        # Build result
        result = {
            "request": {
                "annotator_id": request.annotator_id,
                "domain": request.domain,
                "sample_text": request.sample_text,
                "prompt_source": prompt_source,
                "prompt_template": prompt_template,
                "formatted_prompt": prompt,
                "model": model_name,
                "api_key_masked": api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
            },
            "response": {
                "success": error is None,
                "raw_response": response_text,
                "error": error,
                "parsed_label": label,
                "parsing_error": parsing_error,
                "validity_error": validity_error,
                "malformed": (parsing_error is not None) or (validity_error is not None)
            }
        }

        if error:
            print(f"   ❌ Error: {error}")
        else:
            print(f"   ✅ Success! Label: {label}, Malformed: {result['response']['malformed']}")

        return APIResponse(
            success=True,
            data=result,
            message="Gemini API test completed"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        raise HTTPException(500, str(e))


@router.get("/system-status")
async def get_system_status():
    """
    Get comprehensive system status for debugging.

    Returns information about:
    - Running workers
    - Process registry state
    - File system state (data directories)
    """
    try:
        base_dir = Path(__file__).parent.parent.parent

        # Get running workers from ProcessRegistry
        registry = ProcessRegistry()
        running_workers = registry.get_running_workers()
        all_workers = registry.get_all_workers()
        orphaned = registry.get_orphaned_workers()

        # Check data directories
        data_dirs = {
            "annotations": (base_dir / "data" / "annotations").exists(),
            "logs": (base_dir / "data" / "logs").exists(),
            "heartbeats": (base_dir / "data" / "heartbeats").exists(),
            "process_registry": (base_dir / "data" / "process_registry").exists(),
            "rate_limiter": (base_dir / "data" / "rate_limiter").exists(),
        }

        # Count files in each directory
        file_counts = {}
        for dir_name, exists in data_dirs.items():
            if exists:
                dir_path = base_dir / "data" / dir_name
                file_counts[dir_name] = len(list(dir_path.rglob("*"))) if dir_path.exists() else 0
            else:
                file_counts[dir_name] = 0

        status = {
            "workers": {
                "running_count": len(running_workers),
                "registered_count": len(all_workers),
                "orphaned_count": len(orphaned),
                "running_workers": running_workers,
                "orphaned_workers": [{"annotator_id": a, "domain": d} for a, d in orphaned]
            },
            "data_directories": data_dirs,
            "file_counts": file_counts,
            "system_info": {
                "base_dir": str(base_dir),
                "config_exists": (base_dir / "config" / "settings.json").exists(),
                "api_keys_exists": (base_dir / "config" / "api_keys.json").exists(),
            }
        }

        return APIResponse(
            success=True,
            data=status,
            message="System status retrieved"
        )

    except Exception as e:
        raise HTTPException(500, str(e))
