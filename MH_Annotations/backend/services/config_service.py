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
from backend.core.dataset_loader import DatasetLoader


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
        self.prompts_versions_dir = self.config_dir / "prompts" / "versions"
        self.active_versions_path = self.config_dir / "prompts" / "active_versions.json"

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

    def update_domain_config(self, annotator_id: int, domain: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration for specific annotator-domain pair and return updated config."""
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
        # Return the updated config
        return settings["annotators"][annotator_key][domain]

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
        # Check for active version first
        active_filename = self.get_active_version_filename(annotator_id, domain)

        if active_filename:
            # Load active version
            version_path = self.prompts_versions_dir / f"annotator_{annotator_id}" / domain / active_filename
            if version_path.exists():
                content = version_path.read_text(encoding='utf-8')
                stat = version_path.stat()

                # Parse version metadata
                try:
                    parts = version_path.stem.split('_')
                    version_number = int(parts[0][1:])
                    timestamp_parts = parts[-3:]
                    name_parts = parts[1:-3]
                    version_name = '_'.join(name_parts)

                    return {
                        "content": content,
                        "is_override": True,
                        "source_type": "version",
                        "active_version": active_filename,
                        "version_metadata": {
                            "version_number": version_number,
                            "version_name": version_name,
                            "timestamp": '_'.join(timestamp_parts).replace('_', ' ').replace('-', ':')
                        },
                        "source_path": str(version_path.relative_to(self.base_dir)),
                        "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                except (ValueError, IndexError):
                    # Fallback if parsing fails
                    return {
                        "content": content,
                        "is_override": True,
                        "source_type": "version",
                        "active_version": active_filename,
                        "source_path": str(version_path.relative_to(self.base_dir)),
                        "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }

        # Check for legacy override (backward compatibility)
        override_path = self.prompts_override_dir / f"annotator_{annotator_id}" / f"{domain}.txt"
        if override_path.exists():
            content = override_path.read_text(encoding='utf-8')
            stat = override_path.stat()
            return {
                "content": content,
                "is_override": True,
                "source_type": "override",
                "source_path": str(override_path.relative_to(self.base_dir)),
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }

        # Fall back to base
        base_path = self.prompts_base_dir / f"{domain}.txt"
        if not base_path.exists():
            raise FileNotFoundError(f"Prompt not found for domain: {domain}")
        content = base_path.read_text(encoding='utf-8')
        stat = base_path.stat()
        return {
            "content": content,
            "is_override": False,
            "source_type": "base",
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

    # ===========================
    # Phase 3 - Version Management Methods
    # ===========================

    def _sanitize_version_name(self, name: str) -> str:
        """Sanitize version name: remove special chars, convert spaces to underscores."""
        import re
        # Remove special chars, keep only alphanumeric and underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Limit length
        return sanitized[:50]

    def _get_next_version_number(self, annotator_id: int, domain: str) -> int:
        """Get next version number for annotator-domain pair."""
        version_dir = self.prompts_versions_dir / f"annotator_{annotator_id}" / domain
        if not version_dir.exists():
            return 1

        # Find highest version number
        max_version = 0
        for file in version_dir.glob("v*.txt"):
            try:
                # Extract version number from filename like "v2_name_timestamp.txt"
                version_num = int(file.name.split('_')[0][1:])
                max_version = max(max_version, version_num)
            except (ValueError, IndexError):
                continue

        return max_version + 1

    def get_active_version_filename(self, annotator_id: int, domain: str) -> Optional[str]:
        """Get currently active version filename from active_versions.json."""
        active_versions = atomic_read_json(str(self.active_versions_path))
        if not active_versions:
            return None

        annotator_key = f"annotator_{annotator_id}"
        if annotator_key not in active_versions:
            return None

        return active_versions[annotator_key].get(domain)

    def set_active_version(self, annotator_id: int, domain: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """Set which version is active for annotator-domain."""
        # Validate file exists if not None
        if filename is not None:
            version_path = self.prompts_versions_dir / f"annotator_{annotator_id}" / domain / filename
            if not version_path.exists():
                raise FileNotFoundError(f"Version file not found: {filename}")

        # Load active versions
        active_versions = atomic_read_json(str(self.active_versions_path))
        if not active_versions:
            active_versions = {}

        # Ensure structure exists
        annotator_key = f"annotator_{annotator_id}"
        if annotator_key not in active_versions:
            active_versions[annotator_key] = {
                "urgency": None,
                "therapeutic": None,
                "intensity": None,
                "adjunct": None,
                "modality": None,
                "redressal": None
            }

        # Update active version
        active_versions[annotator_key][domain] = filename

        # Save atomically
        atomic_write_json(active_versions, str(self.active_versions_path))

        return {
            "annotator_id": str(annotator_id),
            "domain": domain,
            "active_version": filename,
            "message": "Active version updated successfully"
        }

    def save_prompt_version(self, annotator_id: int, domain: str,
                           version_name: str, content: str,
                           description: Optional[str] = None) -> Dict[str, Any]:
        """Save a new prompt version."""
        # Sanitize version name
        sanitized_name = self._sanitize_version_name(version_name)

        # Get next version number
        version_number = self._get_next_version_number(annotator_id, domain)

        # Generate timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Generate filename
        filename = f"v{version_number}_{sanitized_name}_{timestamp}.txt"

        # Create directory if needed
        version_dir = self.prompts_versions_dir / f"annotator_{annotator_id}" / domain
        version_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        version_path = version_dir / filename
        version_path.write_text(content, encoding='utf-8')

        return {
            "filename": filename,
            "version_number": version_number,
            "saved_path": str(version_path.relative_to(self.base_dir)),
            "timestamp": datetime.now().isoformat()
        }

    def list_prompt_versions(self, annotator_id: int, domain: str) -> Dict[str, Any]:
        """List all versions for annotator-domain including base."""
        result = {
            "base": None,
            "versions": []
        }

        # Get base prompt info
        base_path = self.prompts_base_dir / f"{domain}.txt"
        if base_path.exists():
            content = base_path.read_text(encoding='utf-8')
            stat = base_path.stat()
            result["base"] = {
                "filename": "base",
                "display_name": "Base Prompt (Default)",
                "is_active": False,
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
                "character_count": len(content),
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }

        # Get active version
        active_filename = self.get_active_version_filename(annotator_id, domain)

        # Mark base as active if no active version
        if result["base"] and active_filename is None:
            result["base"]["is_active"] = True

        # Get all versions
        version_dir = self.prompts_versions_dir / f"annotator_{annotator_id}" / domain
        if version_dir.exists():
            for version_file in sorted(version_dir.glob("v*.txt"), reverse=True):
                try:
                    # Parse filename: v{num}_{name}_{timestamp}.txt
                    parts = version_file.stem.split('_')
                    version_number = int(parts[0][1:])

                    # Extract name and timestamp
                    # Find timestamp part (last 3 parts: YYYY-MM-DD_HH-MM-SS)
                    timestamp_parts = parts[-3:]
                    timestamp_str = '_'.join(timestamp_parts)

                    # Name is everything between version number and timestamp
                    name_parts = parts[1:-3]
                    version_name = '_'.join(name_parts)

                    # Read content
                    content = version_file.read_text(encoding='utf-8')

                    # Create display name
                    display_name = version_name.replace('_', ' ').title()

                    version_info = {
                        "filename": version_file.name,
                        "version_number": version_number,
                        "version_name": version_name,
                        "display_name": display_name,
                        "is_active": version_file.name == active_filename,
                        "timestamp": timestamp_str.replace('_', ' ').replace('-', ':'),
                        "content_preview": content[:100] + "..." if len(content) > 100 else content,
                        "character_count": len(content),
                        "description": description if 'description' in locals() else None
                    }

                    result["versions"].append(version_info)

                except (ValueError, IndexError) as e:
                    # Skip malformed filenames
                    continue

        return result

    def get_version_content(self, annotator_id: int, domain: str, filename: str) -> Dict[str, Any]:
        """Get full content of a specific version."""
        version_path = self.prompts_versions_dir / f"annotator_{annotator_id}" / domain / filename

        if not version_path.exists():
            raise FileNotFoundError(f"Version not found: {filename}")

        content = version_path.read_text(encoding='utf-8')

        # Parse filename to extract metadata
        try:
            parts = version_path.stem.split('_')
            version_number = int(parts[0][1:])

            # Extract timestamp
            timestamp_parts = parts[-3:]
            timestamp_str = '_'.join(timestamp_parts)

            # Extract name
            name_parts = parts[1:-3]
            version_name = '_'.join(name_parts)

            return {
                "filename": filename,
                "content": content,
                "metadata": {
                    "version_number": version_number,
                    "version_name": version_name,
                    "timestamp": timestamp_str.replace('_', ' ').replace('-', ':'),
                    "character_count": len(content),
                    "line_count": content.count('\n') + 1
                }
            }
        except (ValueError, IndexError):
            # Fallback if filename parsing fails
            return {
                "filename": filename,
                "content": content,
                "metadata": {
                    "character_count": len(content),
                    "line_count": content.count('\n') + 1
                }
            }

    def delete_prompt_version(self, annotator_id: int, domain: str, filename: str) -> bool:
        """Delete a prompt version file."""
        # Check if version is currently active
        active_filename = self.get_active_version_filename(annotator_id, domain)
        if active_filename == filename:
            raise ValueError("Cannot delete active version. Switch to another version first.")

        # Delete file
        version_path = self.prompts_versions_dir / f"annotator_{annotator_id}" / domain / filename
        if not version_path.exists():
            raise FileNotFoundError(f"Version not found: {filename}")

        version_path.unlink()
        return True

    def get_dataset_info(self) -> Dict[str, Any]:
        """
        Get information about the source dataset.

        Returns:
            Dict with dataset information including:
                - total_rows: Number of samples in dataset
                - file_path: Relative path to dataset file
                - file_exists: Whether file exists
                - last_modified: ISO timestamp of file modification
                - file_size_mb: File size in megabytes

        Raises:
            FileNotFoundError: If dataset file doesn't exist
            Exception: If dataset cannot be read
        """
        dataset_path = self.base_dir / "data" / "source" / "m_help_dataset.xlsx"

        # Check if file exists
        if not dataset_path.exists():
            raise FileNotFoundError(
                f"Dataset file not found at: {dataset_path}. "
                f"Please ensure m_help_dataset.xlsx exists in data/source/ directory."
            )

        try:
            # Initialize dataset loader
            dataset_loader = DatasetLoader(str(dataset_path))

            # Load dataset and get count
            # This will use the cached dataset if already loaded
            total_rows = dataset_loader.get_total_count()

            # Get file metadata
            stat = dataset_path.stat()

            return {
                "total_rows": total_rows,
                "file_path": str(dataset_path.relative_to(self.base_dir)),
                "file_exists": True,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "file_size_mb": round(stat.st_size / (1024 * 1024), 2)
            }

        except FileNotFoundError:
            # Re-raise FileNotFoundError as-is
            raise
        except Exception as e:
            # Wrap other exceptions with context
            raise Exception(f"Failed to read dataset: {str(e)}")

    def test_api_key(self, annotator_id: int, api_key: str) -> Dict[str, Any]:
        """
        Test API key by making a real call to Google Gemini API.

        Args:
            annotator_id: Annotator ID (for logging/context)
            api_key: The API key to test

        Returns:
            Dict with:
                - success: bool - Whether the key is valid
                - message: str - User-friendly message
                - error_details: Optional[str] - Technical error details
        """
        from google import genai
        from google.genai import types

        # Get model name from settings
        try:
            settings = self.get_settings()
            model_name = settings.get("global", {}).get("model_name", "gemma-3-27b-it")
        except:
            model_name = "gemma-3-27b-it"

        try:
            # Initialize Gemini client with the API key
            client = genai.Client(api_key=api_key)

            # Create minimal test request
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="Hi")]
                )
            ]

            config = types.GenerateContentConfig()

            # Make a test API call with timeout
            # We use generate_content (non-streaming) for faster testing
            response_text = ""
            try:
                # Use streaming but only collect first chunk for speed
                chunk_count = 0
                for chunk in client.models.generate_content_stream(
                    model=model_name,
                    contents=contents,
                    config=config
                ):
                    if chunk.text:
                        response_text += chunk.text
                        chunk_count += 1
                        # Only need one chunk to verify key works
                        if chunk_count >= 1:
                            break
            except StopIteration:
                pass  # No more chunks, which is fine

            # If we got here without exception, the key is valid
            return {
                "success": True,
                "message": f"API key is valid! Successfully connected to Gemini API with model '{model_name}'",
                "error_details": None
            }

        except Exception as e:
            error_str = str(e).lower()

            # Check for invalid API key errors (401/403)
            if "403" in error_str or "401" in error_str or "api key" in error_str or "permission" in error_str or "unauthorized" in error_str:
                return {
                    "success": False,
                    "message": "Invalid API key - please check the key and try again",
                    "error_details": str(e)
                }

            # Check for rate limit errors (429)
            if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                return {
                    "success": False,
                    "message": "Rate limit exceeded - please try again later",
                    "error_details": str(e)
                }

            # Check for model access errors
            if "model" in error_str and ("not found" in error_str or "not available" in error_str or "not accessible" in error_str):
                return {
                    "success": False,
                    "message": f"Model '{model_name}' not accessible with this key - check your API key permissions",
                    "error_details": str(e)
                }

            # Check for timeout errors
            if "timeout" in error_str or "timed out" in error_str:
                return {
                    "success": False,
                    "message": "Request timeout - please check your internet connection",
                    "error_details": str(e)
                }

            # Generic API error
            return {
                "success": False,
                "message": f"API test failed: {str(e)}",
                "error_details": str(e)
            }
