"""
Worker process management service.
"""

import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.worker_manager import WorkerManager


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
