"""
Configuration validation using Pydantic models.

Validates settings.json structure and values to catch errors early.
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field, validator, ValidationError
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.utils.file_operations import atomic_read_json


class GlobalConfig(BaseModel):
    """Global configuration settings."""

    model_name: str = Field(..., description="Model name for Gemini API")
    request_delay_seconds: float = Field(
        default=2.0,
        ge=0.1,
        le=60.0,
        description="Delay between API requests"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Max retry attempts for failed requests"
    )
    crash_detection_minutes: float = Field(
        default=5.0,
        ge=1.0,
        le=60.0,
        description="Minutes before considering worker crashed"
    )
    control_check_iterations: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Check control signals every N iterations"
    )
    control_check_seconds: int = Field(
        default=10,
        ge=1,
        le=300,
        description="Check control signals every N seconds"
    )

    @validator('model_name')
    def validate_model_name(cls, v):
        if not v or v.strip() == "":
            raise ValueError("model_name cannot be empty")
        return v


class DomainConfig(BaseModel):
    """Configuration for a single domain."""

    enabled: bool = Field(..., description="Whether this domain is enabled")
    target_count: int = Field(
        ...,
        ge=0,
        le=100000,
        description="Target number of samples to annotate"
    )

    @validator('target_count')
    def validate_target_count(cls, v, values):
        if v < 0:
            raise ValueError("target_count cannot be negative")
        if v > 100000:
            raise ValueError("target_count cannot exceed 100000")
        return v


class AnnotatorConfig(BaseModel):
    """Configuration for a single annotator."""

    urgency: DomainConfig
    therapeutic: DomainConfig
    intensity: DomainConfig
    adjunct: DomainConfig
    modality: DomainConfig
    redressal: DomainConfig

    def get_enabled_domains(self) -> list[str]:
        """Get list of enabled domain names."""
        enabled = []
        for domain_name in ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]:
            domain_config = getattr(self, domain_name)
            if domain_config.enabled:
                enabled.append(domain_name)
        return enabled

    def get_total_target(self) -> int:
        """Get total target count across all enabled domains."""
        total = 0
        for domain_name in ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]:
            domain_config = getattr(self, domain_name)
            if domain_config.enabled:
                total += domain_config.target_count
        return total


class Settings(BaseModel):
    """Complete settings configuration."""

    global_config: GlobalConfig = Field(..., alias="global")
    annotators: Dict[str, AnnotatorConfig]

    class Config:
        populate_by_name = True

    @validator('annotators')
    def validate_annotators(cls, v):
        # Check that we have annotators 1-5
        required_ids = {"1", "2", "3", "4", "5"}
        actual_ids = set(v.keys())

        missing = required_ids - actual_ids
        if missing:
            raise ValueError(f"Missing annotator configurations: {missing}")

        extra = actual_ids - required_ids
        if extra:
            raise ValueError(f"Unexpected annotator IDs: {extra}")

        return v

    def get_enabled_workers(self) -> list[tuple[int, str]]:
        """Get list of (annotator_id, domain) tuples for all enabled workers."""
        enabled_workers = []

        for annotator_id_str, annotator_config in self.annotators.items():
            annotator_id = int(annotator_id_str)
            for domain in annotator_config.get_enabled_domains():
                enabled_workers.append((annotator_id, domain))

        return enabled_workers

    def get_total_enabled_count(self) -> int:
        """Get total number of enabled worker configurations."""
        return len(self.get_enabled_workers())

    def get_total_target_samples(self) -> int:
        """Get total target samples across all enabled workers."""
        total = 0
        for annotator_config in self.annotators.values():
            total += annotator_config.get_total_target()
        return total


class APIKeysConfig(BaseModel):
    """API keys configuration."""

    annotator_1: Optional[str] = None
    annotator_2: Optional[str] = None
    annotator_3: Optional[str] = None
    annotator_4: Optional[str] = None
    annotator_5: Optional[str] = None

    @validator('annotator_1', 'annotator_2', 'annotator_3', 'annotator_4', 'annotator_5')
    def validate_api_key(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError("API key cannot be empty string")
        return v

    def get_missing_keys(self, required_annotator_ids: list[int]) -> list[int]:
        """Get list of annotator IDs that are missing API keys."""
        missing = []
        for annotator_id in required_annotator_ids:
            key = getattr(self, f"annotator_{annotator_id}")
            if not key or key.strip() == "":
                missing.append(annotator_id)
        return missing


class ConfigValidator:
    """
    Validates configuration files.

    Usage:
        validator = ConfigValidator()
        is_valid, errors = validator.validate_all()
        if not is_valid:
            print("Configuration errors:", errors)
    """

    def __init__(self):
        """Initialize configuration validator."""
        self.base_dir = Path(__file__).parent.parent.parent

    def validate_settings(self) -> tuple[bool, Optional[Settings], list[str]]:
        """
        Validate settings.json.

        Returns:
            Tuple of (is_valid, settings_obj, error_messages)
        """
        settings_path = self.base_dir / "config" / "settings.json"
        errors = []

        # Check file exists
        if not settings_path.exists():
            return False, None, [f"Settings file not found: {settings_path}"]

        # Load JSON
        try:
            data = atomic_read_json(str(settings_path))
            if data is None:
                return False, None, ["Settings file is empty or invalid JSON"]
        except Exception as e:
            return False, None, [f"Failed to read settings file: {str(e)}"]

        # Validate with Pydantic
        try:
            settings = Settings(**data)
            return True, settings, []
        except ValidationError as e:
            for error in e.errors():
                field = " -> ".join(str(x) for x in error["loc"])
                message = error["msg"]
                errors.append(f"{field}: {message}")
            return False, None, errors

    def validate_api_keys(self, settings: Optional[Settings] = None) -> tuple[bool, Optional[APIKeysConfig], list[str]]:
        """
        Validate api_keys.json.

        Args:
            settings: Optional Settings object to check which keys are required

        Returns:
            Tuple of (is_valid, api_keys_obj, error_messages)
        """
        api_keys_path = self.base_dir / "config" / "api_keys.json"
        errors = []

        # Check file exists
        if not api_keys_path.exists():
            return False, None, [f"API keys file not found: {api_keys_path}"]

        # Load JSON
        try:
            data = atomic_read_json(str(api_keys_path))
            if data is None:
                return False, None, ["API keys file is empty or invalid JSON"]
        except Exception as e:
            return False, None, [f"Failed to read API keys file: {str(e)}"]

        # Validate with Pydantic
        try:
            api_keys = APIKeysConfig(**data)
        except ValidationError as e:
            for error in e.errors():
                field = " -> ".join(str(x) for x in error["loc"])
                message = error["msg"]
                errors.append(f"{field}: {message}")
            return False, None, errors

        # Check if required keys are present (based on enabled workers)
        if settings:
            enabled_workers = settings.get_enabled_workers()
            required_annotator_ids = list(set(ann_id for ann_id, _ in enabled_workers))
            missing_keys = api_keys.get_missing_keys(required_annotator_ids)

            if missing_keys:
                errors.append(
                    f"Missing API keys for enabled annotators: {missing_keys}"
                )
                return False, api_keys, errors

        return True, api_keys, []

    def validate_all(self) -> tuple[bool, dict, list[str]]:
        """
        Validate all configuration files.

        Returns:
            Tuple of (is_valid, config_objects, all_errors)
        """
        all_errors = []
        config_objects = {}

        # Validate settings
        settings_valid, settings_obj, settings_errors = self.validate_settings()
        if not settings_valid:
            all_errors.extend([f"Settings: {err}" for err in settings_errors])
        else:
            config_objects["settings"] = settings_obj

        # Validate API keys
        api_keys_valid, api_keys_obj, api_keys_errors = self.validate_api_keys(settings_obj)
        if not api_keys_valid:
            all_errors.extend([f"API Keys: {err}" for err in api_keys_errors])
        else:
            config_objects["api_keys"] = api_keys_obj

        is_valid = settings_valid and api_keys_valid
        return is_valid, config_objects, all_errors

    def get_validation_summary(self) -> dict:
        """
        Get validation summary with statistics.

        Returns:
            Dictionary with validation results and statistics
        """
        is_valid, config_objects, errors = self.validate_all()

        summary = {
            "is_valid": is_valid,
            "errors": errors,
            "error_count": len(errors)
        }

        if "settings" in config_objects:
            settings = config_objects["settings"]
            summary["statistics"] = {
                "enabled_workers": settings.get_total_enabled_count(),
                "total_target_samples": settings.get_total_target_samples(),
                "enabled_worker_list": settings.get_enabled_workers()
            }

        return summary
