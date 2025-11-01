"""
Worker process management service.
"""

import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.worker_manager import WorkerManager
from backend.utils.file_operations import atomic_read_json


class WorkerService:
    """Service for managing worker processes."""

    def __init__(self):
        """Initialize worker service."""
        self.worker_manager = WorkerManager()
        self.base_dir = Path(__file__).parent.parent.parent
        self.domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]

    def start_workers(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Start worker(s) based on filters."""
        results = []
        annotator_id = filters.get("annotator_id")
        domain = filters.get("domain")

        if annotator_id and domain:
            # Single worker
            result = self.worker_manager.start_worker(annotator_id, domain)
            results.append(result)
        elif annotator_id:
            # All domains for this annotator
            for d in self.domains:
                result = self.worker_manager.start_worker(annotator_id, d)
                results.append(result)
        elif domain:
            # This domain for all annotators
            for ann_id in [1, 2, 3, 4, 5]:
                result = self.worker_manager.start_worker(ann_id, domain)
                results.append(result)
        else:
            # All enabled workers
            result = self.worker_manager.start_all_enabled()
            # Convert to list format
            for ann_id in [1, 2, 3, 4, 5]:
                for d in self.domains:
                    results.append({
                        "annotator": ann_id,
                        "domain": d,
                        "status": "check_system_for_status"
                    })

        return results

    def stop_workers(self, filters: Dict[str, Any], timeout: int = 30) -> List[Dict[str, Any]]:
        """Stop worker(s) based on filters."""
        results = []
        annotator_id = filters.get("annotator_id")
        domain = filters.get("domain")

        if annotator_id and domain:
            result = self.worker_manager.stop_worker(annotator_id, domain, timeout)
            results.append(result)
        elif annotator_id:
            for d in self.domains:
                result = self.worker_manager.stop_worker(annotator_id, d, timeout)
                results.append(result)
        elif domain:
            for ann_id in [1, 2, 3, 4, 5]:
                result = self.worker_manager.stop_worker(ann_id, domain, timeout)
                results.append(result)
        else:
            self.worker_manager.stop_all_workers(timeout)
            results.append({"status": "all_stopped"})

        return results

    def pause_workers(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Pause worker(s) based on filters."""
        results = []
        annotator_id = filters.get("annotator_id")
        domain = filters.get("domain")

        if annotator_id and domain:
            result = self.worker_manager.pause_worker(annotator_id, domain)
            results.append(result)
        elif annotator_id:
            for d in self.domains:
                result = self.worker_manager.pause_worker(annotator_id, d)
                results.append(result)
        elif domain:
            for ann_id in [1, 2, 3, 4, 5]:
                result = self.worker_manager.pause_worker(ann_id, domain)
                results.append(result)
        else:
            for ann_id in [1, 2, 3, 4, 5]:
                for d in self.domains:
                    result = self.worker_manager.pause_worker(ann_id, d)
                    results.append(result)

        return results

    def resume_workers(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Resume worker(s) based on filters."""
        results = []
        annotator_id = filters.get("annotator_id")
        domain = filters.get("domain")

        if annotator_id and domain:
            result = self.worker_manager.resume_worker(annotator_id, domain)
            results.append(result)
        elif annotator_id:
            for d in self.domains:
                result = self.worker_manager.resume_worker(annotator_id, d)
                results.append(result)
        elif domain:
            for ann_id in [1, 2, 3, 4, 5]:
                result = self.worker_manager.resume_worker(ann_id, domain)
                results.append(result)
        else:
            for ann_id in [1, 2, 3, 4, 5]:
                for d in self.domains:
                    result = self.worker_manager.resume_worker(ann_id, d)
                    results.append(result)

        return results

    def reset_data(self, scope: str, annotator_id: Optional[int] = None, domain: Optional[str] = None) -> Dict[str, Any]:
        """Reset annotation data."""
        deleted_files = []
        deleted_workers = 0
        deleted_samples = 0

        if scope == "single":
            if not annotator_id or not domain:
                raise ValueError("annotator_id and domain required for single scope")

            # Delete annotations directory
            ann_dir = self.base_dir / "data" / "annotations" / f"annotator_{annotator_id}" / domain
            if ann_dir.exists():
                # Count files before deletion
                for f in ann_dir.rglob("*"):
                    if f.is_file():
                        deleted_files.append(str(f.relative_to(self.base_dir)))
                shutil.rmtree(ann_dir)
                deleted_workers = 1

            # Delete control file
            control_file = self.base_dir / "control" / f"annotator_{annotator_id}_{domain}.json"
            if control_file.exists():
                control_file.unlink()
                deleted_files.append(str(control_file.relative_to(self.base_dir)))

        elif scope == "all":
            # Delete all annotations
            ann_base = self.base_dir / "data" / "annotations"
            if ann_base.exists():
                for f in ann_base.rglob("*"):
                    if f.is_file():
                        deleted_files.append(str(f.relative_to(self.base_dir)))
                shutil.rmtree(ann_base)
                ann_base.mkdir(parents=True, exist_ok=True)
                deleted_workers = 30

            # Delete all logs
            logs_dir = self.base_dir / "data" / "logs"
            if logs_dir.exists():
                for f in logs_dir.rglob("*"):
                    if f.is_file():
                        deleted_files.append(str(f.relative_to(self.base_dir)))
                shutil.rmtree(logs_dir)
                logs_dir.mkdir(parents=True, exist_ok=True)

            # Delete all control files
            control_dir = self.base_dir / "control"
            if control_dir.exists():
                for f in control_dir.glob("*.json"):
                    f.unlink()
                    deleted_files.append(str(f.relative_to(self.base_dir)))

        return {
            "deleted_workers": deleted_workers,
            "deleted_samples": deleted_samples,  # Would need to count lines in JSONL
            "deleted_files": deleted_files
        }

    def validate_run_start(self) -> Dict[str, Any]:
        """
        Validate that a run can be started.

        Returns dict with:
        - valid: bool
        - errors: List[str]
        - warnings: List[str]
        - enabled_workers: List[dict]
        """
        errors = []
        warnings = []
        enabled_workers = []

        # Load settings
        settings_path = self.base_dir / "config" / "settings.json"
        settings = atomic_read_json(str(settings_path))

        if not settings:
            errors.append("Settings file not found")
            return {"valid": False, "errors": errors, "warnings": warnings, "enabled_workers": []}

        # Load API keys
        api_keys_path = self.base_dir / "config" / "api_keys.json"
        api_keys = atomic_read_json(str(api_keys_path))

        if not api_keys:
            api_keys = {}

        # Check dataset
        dataset_path = self.base_dir / "data" / "source" / "m_help_dataset.xlsx"
        if not dataset_path.exists():
            errors.append(f"Dataset file not found: {dataset_path}")

        # Check each annotator-domain pair
        has_any_enabled = False

        for annotator_id in [1, 2, 3, 4, 5]:
            for domain in self.domains:
                # Check if enabled
                try:
                    domain_config = settings["annotators"][str(annotator_id)][domain]
                    enabled = domain_config.get("enabled", False)
                    target_count = domain_config.get("target_count", 0)
                except KeyError:
                    continue

                if not enabled:
                    continue

                has_any_enabled = True

                # Check API key
                api_key = api_keys.get(f"annotator_{annotator_id}", "")
                has_api_key = bool(api_key and api_key.strip())

                if not has_api_key:
                    errors.append(f"Annotator {annotator_id}: No API key configured")

                # Check prompt (base or override)
                override_path = self.base_dir / "config" / "prompts" / "overrides" / f"annotator_{annotator_id}" / f"{domain}.txt"
                base_path = self.base_dir / "config" / "prompts" / "base" / f"{domain}.txt"

                has_prompt = override_path.exists() or base_path.exists()

                if not has_prompt:
                    errors.append(f"Annotator {annotator_id}, Domain {domain}: No prompt found")

                # Check target count
                if target_count <= 0:
                    warnings.append(f"Annotator {annotator_id}, Domain {domain}: Target count is 0")

                enabled_workers.append({
                    "annotator_id": annotator_id,
                    "domain": domain,
                    "has_api_key": has_api_key,
                    "has_prompt": has_prompt,
                    "target_count": target_count
                })

        if not has_any_enabled:
            errors.append("No workers are enabled in configuration")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "enabled_workers": enabled_workers
        }

    def get_grid_status(self) -> List[Dict[str, Any]]:
        """
        Get status for all enabled workers in grid display format.

        Only returns enabled workers.
        """
        workers = []

        # Load settings
        settings_path = self.base_dir / "config" / "settings.json"
        settings = atomic_read_json(str(settings_path))

        if not settings:
            return []

        # Get crash detection minutes (not actually needed here but good to have)
        crash_detection_minutes = settings.get("global", {}).get("crash_detection_minutes", 5)

        for annotator_id in [1, 2, 3, 4, 5]:
            for domain in self.domains:
                # Check if enabled
                try:
                    domain_config = settings["annotators"][str(annotator_id)][domain]
                    enabled = domain_config.get("enabled", False)
                    target_count = domain_config.get("target_count", 0)
                except KeyError:
                    continue

                if not enabled:
                    continue

                # Get worker status
                status = self.worker_manager.get_worker_status(annotator_id, domain)

                # Calculate ETA
                speed = status["progress"]["speed"]
                remaining = status["progress"]["target"] - status["progress"]["completed"]
                eta_seconds = None

                if speed > 0:
                    eta_seconds = int((remaining / speed) * 60)

                # Calculate progress percentage
                progress_pct = 0.0
                if status["progress"]["target"] > 0:
                    progress_pct = (status["progress"]["completed"] / status["progress"]["target"]) * 100

                workers.append({
                    "annotator_id": annotator_id,
                    "domain": domain,
                    "status": status["status"],
                    "progress_percentage": round(progress_pct, 1),
                    "completed_count": status["progress"]["completed"],
                    "target_count": status["progress"]["target"],
                    "malformed_count": status["progress"]["malformed"],
                    "speed": round(speed, 2),
                    "eta_seconds": eta_seconds,
                    "is_running": status["running"],
                    "is_stale": status["stale"],
                    "last_updated": status["last_updated"],
                    "pid": status.get("pid")
                })

        return workers

    def factory_reset(self) -> Dict[str, Any]:
        """
        Factory reset - delete ALL data.

        Returns dict with deleted file counts.
        """
        deleted_files = []

        # Delete all annotations
        ann_base = self.base_dir / "data" / "annotations"
        if ann_base.exists():
            for f in ann_base.rglob("*"):
                if f.is_file():
                    deleted_files.append(str(f.relative_to(self.base_dir)))
            shutil.rmtree(ann_base)
            ann_base.mkdir(parents=True, exist_ok=True)

        # Delete all logs
        logs_dir = self.base_dir / "data" / "logs"
        if logs_dir.exists():
            for f in logs_dir.rglob("*"):
                if f.is_file():
                    deleted_files.append(str(f.relative_to(self.base_dir)))
            shutil.rmtree(logs_dir)
            logs_dir.mkdir(parents=True, exist_ok=True)

        # Delete all control files
        control_dir = self.base_dir / "control"
        if control_dir.exists():
            for f in control_dir.glob("*.json"):
                deleted_files.append(str(f.relative_to(self.base_dir)))
                f.unlink()

        # Delete exports directory if exists
        exports_dir = self.base_dir / "data" / "exports"
        if exports_dir.exists():
            for f in exports_dir.rglob("*"):
                if f.is_file():
                    deleted_files.append(str(f.relative_to(self.base_dir)))
            shutil.rmtree(exports_dir)
            exports_dir.mkdir(parents=True, exist_ok=True)

        return {
            "deleted_files_count": len(deleted_files),
            "deleted_files": deleted_files[:50]  # Return first 50 for display
        }
