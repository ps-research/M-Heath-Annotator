"""
Run configuration and management service.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.config_service import ConfigService


class RunService:
    """Service for managing run configurations."""

    def __init__(self):
        """Initialize run service."""
        self.config_service = ConfigService()
        self.base_dir = Path(__file__).parent.parent.parent
        self.domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]

    def get_enabled_workers(self) -> List[Dict[str, Any]]:
        """Get all enabled workers with their full configuration."""
        settings = self.config_service.get_settings()
        api_keys = self.config_service.get_api_keys(masked=False)
        active_versions = self.config_service._load_active_versions()

        enabled_workers = []

        for annotator_id in range(1, 6):
            annotator_key = str(annotator_id)
            annotator_config = settings.get("annotators", {}).get(annotator_key, {})

            for domain in self.domains:
                domain_config = annotator_config.get(domain, {})

                if domain_config.get("enabled", False):
                    # Get prompt content
                    prompt = self.config_service.get_prompt(annotator_id, domain)

                    worker_config = {
                        "annotator_id": annotator_id,
                        "domain": domain,
                        "target_count": domain_config.get("target_count", 0),
                        "enabled": True,
                        "global_settings": settings.get("global", {}),
                        "has_api_key": f"annotator_{annotator_id}" in api_keys and bool(api_keys[f"annotator_{annotator_id}"]),
                        "prompt_info": {
                            "is_override": prompt.get("is_override", False),
                            "source_type": prompt.get("source_type", "base"),
                            "active_version": prompt.get("active_version"),
                            "last_modified": prompt.get("last_modified"),
                            "content_preview": prompt.get("content", "")[:200] + "..." if len(prompt.get("content", "")) > 200 else prompt.get("content", "")
                        }
                    }
                    enabled_workers.append(worker_config)

        return enabled_workers

    def get_annotator_summary(self, annotator_id: int) -> Dict[str, Any]:
        """Get comprehensive summary for a specific annotator."""
        settings = self.config_service.get_settings()
        api_keys = self.config_service.get_api_keys(masked=False)

        annotator_key = str(annotator_id)
        annotator_config = settings.get("annotators", {}).get(annotator_key, {})

        enabled_domains = []
        total_target = 0

        for domain in self.domains:
            domain_config = annotator_config.get(domain, {})

            if domain_config.get("enabled", False):
                prompt = self.config_service.get_prompt(annotator_id, domain)

                enabled_domains.append({
                    "domain": domain,
                    "target_count": domain_config.get("target_count", 0),
                    "prompt_info": {
                        "source_type": prompt.get("source_type", "base"),
                        "active_version": prompt.get("active_version"),
                        "content_preview": prompt.get("content", "")[:100] + "..." if len(prompt.get("content", "")) > 100 else prompt.get("content", "")
                    }
                })
                total_target += domain_config.get("target_count", 0)

        return {
            "annotator_id": annotator_id,
            "has_api_key": f"annotator_{annotator_id}" in api_keys and bool(api_keys[f"annotator_{annotator_id}"]),
            "global_settings": settings.get("global", {}),
            "enabled_domains": enabled_domains,
            "total_target_count": total_target,
            "enabled_count": len(enabled_domains)
        }

    def get_all_annotator_summaries(self) -> List[Dict[str, Any]]:
        """Get summaries for all annotators."""
        summaries = []
        for annotator_id in range(1, 6):
            summary = self.get_annotator_summary(annotator_id)
            # Only include annotators with at least one enabled domain
            if summary["enabled_count"] > 0:
                summaries.append(summary)

        return summaries
