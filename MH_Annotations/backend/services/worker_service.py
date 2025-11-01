"""
Worker process management service.
"""

import shutil
import time
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, List, Any, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.worker_manager import WorkerManager
from backend.core.db_manager import get_db
from backend.utils.file_operations import atomic_write_json


class WorkerService:
    """Service for managing worker processes."""

    def __init__(self):
        """Initialize worker service."""
        self.worker_manager = WorkerManager()
        self.db = get_db()
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
        """
        Reset annotation data using database.

        Scope:
            - "single": Reset specific worker
            - "all": Factory reset - clear all data
        """
        deleted_files = []
        deleted_workers = 0
        deleted_samples = 0

        if scope == "single":
            if not annotator_id or not domain:
                raise ValueError("annotator_id and domain required for single scope")

            print(f"🧹 Resetting worker {annotator_id}/{domain}...")

            # Reset worker in database
            self.db.reset_worker(annotator_id, domain)
            deleted_workers = 1

            # Delete annotations JSONL file
            ann_file = self.base_dir / "data" / "annotations" / f"annotator_{annotator_id}" / domain / "annotations.jsonl"
            if ann_file.exists():
                ann_file.unlink()
                deleted_files.append(str(ann_file.relative_to(self.base_dir)))

            # Delete control file
            control_file = self.base_dir / "control" / f"annotator_{annotator_id}_{domain}.json"
            if control_file.exists():
                control_file.unlink()
                deleted_files.append(str(control_file.relative_to(self.base_dir)))

            print(f"   ✓ Worker {annotator_id}/{domain} reset")

        elif scope == "all":
            print("🧹 FACTORY RESET: Cleaning up system state...")

            # Step 1 - Close all log file handlers to release locks
            print("   Closing all log file handlers...")
            loggers_to_close = []
            for name in list(logging.Logger.manager.loggerDict.keys()):
                if name.startswith("worker.") or name in ["worker_manager", "watchdog", "api", "gemini_api"]:
                    logger = logging.getLogger(name)
                    loggers_to_close.append(logger)

            # Close all file handlers
            for logger in loggers_to_close:
                for handler in logger.handlers[:]:
                    if isinstance(handler, logging.handlers.RotatingFileHandler):
                        try:
                            handler.close()
                            logger.removeHandler(handler)
                        except:
                            pass

            print("   ✓ Log handlers closed")

            # Step 2 - Factory reset database (preserves configuration)
            print("   Resetting database...")
            try:
                self.db.factory_reset()
                deleted_workers = 30
                print("   ✓ Database reset completed")
            except Exception as e:
                print(f"   ⚠️  Error resetting database: {e}")

            # Step 3 - Delete all annotation JSONL files
            print("   Deleting annotation files...")
            ann_base = self.base_dir / "data" / "annotations"
            if ann_base.exists():
                try:
                    for f in ann_base.rglob("*.jsonl"):
                        if f.is_file():
                            f.unlink()
                            deleted_files.append(str(f.relative_to(self.base_dir)))
                    print("   ✓ Annotation files deleted")
                except OSError as e:
                    print(f"   ⚠️  Error deleting annotations: {e}")

            # Step 4 - Delete all logs (with retry for locked files)
            print("   Deleting logs...")
            logs_dir = self.base_dir / "data" / "logs"
            if logs_dir.exists():
                try:
                    # Give OS time to release file handles
                    time.sleep(1)
                    for f in logs_dir.rglob("*"):
                        if f.is_file():
                            deleted_files.append(str(f.relative_to(self.base_dir)))
                    shutil.rmtree(logs_dir)
                    logs_dir.mkdir(parents=True, exist_ok=True)
                    print("   ✓ Logs deleted")
                except OSError as e:
                    print(f"   ⚠️  Error deleting logs (files may be locked): {e}")
                    # Try individual file deletion
                    for f in logs_dir.rglob("*"):
                        if f.is_file():
                            try:
                                f.unlink()
                            except:
                                pass

            # Step 5 - Delete all control files
            print("   Deleting control files...")
            control_dir = self.base_dir / "control"
            if control_dir.exists():
                for f in control_dir.glob("*.json"):
                    try:
                        f.unlink()
                        deleted_files.append(str(f.relative_to(self.base_dir)))
                    except:
                        pass
                print("   ✓ Control files deleted")

            # Step 6 - Clear rate limiter state
            print("   Clearing rate limiter state...")
            rate_limiter_dir = self.base_dir / "data" / "rate_limiter"
            if rate_limiter_dir.exists():
                try:
                    shutil.rmtree(rate_limiter_dir)
                    rate_limiter_dir.mkdir(parents=True, exist_ok=True)
                    print("   ✓ Rate limiter state cleared")
                except OSError as e:
                    print(f"   ⚠️  Error deleting rate limiter state: {e}")

            print("🎉 Factory reset complete!")

        return {
            "deleted_workers": deleted_workers,
            "deleted_samples": deleted_samples,
            "deleted_files": deleted_files
        }
