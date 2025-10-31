"""
Configuration management service.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.utils.file_operations import atomic_read_json, atomic_write_json


class ConfigService:
    """Service for managing configuration."""

    def __init__(self):
        """Initialize config service."""
        self.base_dir = Path(__file__).parent.parent.parent
        self.config_dir = self.base_dir / "config"
        self.settings_path = self.config_dir / "settings.json"
        self.api_keys_path = self.config_dir / "api_keys.json"
        self.prompts_base_dir = self.config_dir / "prompts" / "base"
        self.prompts_override_dir = self.config_dir / "prompts" / "overrides"

    def get_settings(self) -> Dict[str, Any]:
        """Get current system settings."""
        settings = atomic_read_json(str(self.settings_path))
        if not settings:
            raise FileNotFoundError(f"Settings file not found: {self.settings_path}")
        return settings

    def update_settings(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update system settings."""
        settings = self.get_settings()
        if "global" not in settings:
            settings["global"] = {}
        for key, value in updates.items():
            if value is not None:
                settings["global"][key] = value
        atomic_write_json(settings, str(self.settings_path))
        return settings

    def get_api_keys(self, masked: bool = True) -> Dict[str, str]:
        """Get API keys."""
        keys = atomic_read_json(str(self.api_keys_path))
        if not keys:
            return {}
        if masked:
            masked_keys = {}
            for annotator, key in keys.items():
                if key and len(key) > 12:
                    masked_keys[annotator] = f"{key[:8]}...{key[-4:]}"
                else:
                    masked_keys[annotator] = "***"
            return masked_keys
        return keys

    def update_api_key(self, annotator_id: int, api_key: str) -> None:
        """Update API key for specific annotator."""
        keys = atomic_read_json(str(self.api_keys_path))
        if not keys:
            keys = {}
        key_name = f"annotator_{annotator_id}"
        keys[key_name] = api_key
        atomic_write_json(keys, str(self.api_keys_path))

    def get_domain_config(self, annotator_id: int, domain: str) -> Dict[str, Any]:
        """Get configuration for specific annotator-domain pair."""
        settings = self.get_settings()
        try:
            annotator_key = str(annotator_id)
            config = settings["annotators"][annotator_key][domain]
            return config
        except KeyError:
            raise ValueError(f"Configuration not found for annotator {annotator_id}, domain {domain}")

    def update_domain_config(self, annotator_id: int, domain: str, config: Dict[str, Any]) -> None:
        """Update configuration for specific annotator-domain pair."""
        settings = self.get_settings()
        annotator_key = str(annotator_id)
        if "annotators" not in settings:
            settings["annotators"] = {}
        if annotator_key not in settings["annotators"]:
            settings["annotators"][annotator_key] = {}
        if domain not in settings["annotators"][annotator_key]:
            settings["annotators"][annotator_key][domain] = {}
        for key, value in config.items():
            if value is not None:
                settings["annotators"][annotator_key][domain][key] = value
        atomic_write_json(settings, str(self.settings_path))

    def list_prompts(self) -> Dict[str, Any]:
        """List all prompts with metadata."""
        result = {"base": {}, "overrides": {}}
        if self.prompts_base_dir.exists():
            for prompt_file in self.prompts_base_dir.glob("*.txt"):
                domain = prompt_file.stem
                stat = prompt_file.stat()
                result["base"][domain] = {
                    "length": stat.st_size,
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
        if self.prompts_override_dir.exists():
            for annotator_dir in self.prompts_override_dir.iterdir():
                if annotator_dir.is_dir():
                    annotator_id = annotator_dir.name
                    result["overrides"][annotator_id] = {}
                    for prompt_file in annotator_dir.glob("*.txt"):
                        domain = prompt_file.stem
                        stat = prompt_file.stat()
                        result["overrides"][annotator_id][domain] = {
                            "length": stat.st_size,
                            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                        }
        return result

    def get_prompt(self, annotator_id: int, domain: str) -> Dict[str, Any]:
        """Get prompt content for specific annotator-domain."""
        override_path = self.prompts_override_dir / f"annotator_{annotator_id}" / f"{domain}.txt"
        if override_path.exists():
            content = override_path.read_text(encoding='utf-8')
            stat = override_path.stat()
            return {
                "content": content,
                "is_override": True,
                "source_path": str(override_path.relative_to(self.base_dir)),
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        base_path = self.prompts_base_dir / f"{domain}.txt"
        if not base_path.exists():
            raise FileNotFoundError(f"Prompt not found for domain: {domain}")
        content = base_path.read_text(encoding='utf-8')
        stat = base_path.stat()
        return {
            "content": content,
            "is_override": False,
            "source_path": str(base_path.relative_to(self.base_dir)),
            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }

    def save_prompt_override(self, annotator_id: int, domain: str, content: str) -> None:
        """Save prompt override."""
        override_dir = self.prompts_override_dir / f"annotator_{annotator_id}"
        override_dir.mkdir(parents=True, exist_ok=True)
        override_path = override_dir / f"{domain}.txt"
        override_path.write_text(content, encoding='utf-8')

    def delete_prompt_override(self, annotator_id: int, domain: str) -> None:
        """Delete prompt override."""
        override_path = self.prompts_override_dir / f"annotator_{annotator_id}" / f"{domain}.txt"
        if not override_path.exists():
            raise FileNotFoundError(f"Override not found for annotator {annotator_id}, domain {domain}")
        override_path.unlink()
