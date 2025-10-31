"""
Monitoring and status aggregation service.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.worker_manager import WorkerManager
from backend.utils.file_operations import atomic_read_json


class MonitoringService:
    """Service for monitoring system and worker status."""

    def __init__(self):
        """Initialize monitoring service."""
        self.worker_manager = WorkerManager()
        self.base_dir = Path(__file__).parent.parent.parent
        self.domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]

    def get_system_overview(self) -> Dict[str, Any]:
        """Get high-level system statistics."""
        all_statuses = self.worker_manager.get_all_statuses()

        total_workers = 30
        enabled_workers = 0
        running_workers = 0
        paused_workers = 0
        completed_workers = 0
        crashed_workers = 0
        
        total_completed = 0
        total_target = 0
        speeds = []

        for status in all_statuses:
            if status.get("status") == "running":
                running_workers += 1
            elif status.get("status") == "paused":
                paused_workers += 1
            elif status.get("status") == "completed":
                completed_workers += 1
            elif status.get("status") == "crashed" or status.get("stale"):
                crashed_workers += 1

            progress = status.get("progress", {})
            total_completed += progress.get("completed", 0)
            total_target += progress.get("target", 0)
            speed = progress.get("speed", 0.0)
            if speed > 0:
                speeds.append(speed)

        avg_speed = sum(speeds) / len(speeds) if speeds else 0.0

        # Estimate remaining time
        remaining_samples = total_target - total_completed
        if avg_speed > 0:
            remaining_minutes = remaining_samples / avg_speed
            hours = int(remaining_minutes // 60)
            minutes = int(remaining_minutes % 60)
            est_time = f"{hours}h {minutes}m"
        else:
            est_time = "Unknown"

        total_percentage = (total_completed / total_target * 100) if total_target > 0 else 0.0

        return {
            "total_workers": total_workers,
            "enabled_workers": enabled_workers,
            "running_workers": running_workers,
            "paused_workers": paused_workers,
            "completed_workers": completed_workers,
            "crashed_workers": crashed_workers,
            "total_progress": {
                "completed": total_completed,
                "target": total_target,
                "percentage": round(total_percentage, 2)
            },
            "avg_speed": round(avg_speed, 2),
            "estimated_time_remaining": est_time
        }

    def get_all_worker_statuses(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get status of all workers with optional filters."""
        all_statuses = self.worker_manager.get_all_statuses()

        if not filters:
            return all_statuses

        # Apply filters
        filtered = []
        for status in all_statuses:
            if "annotator_id" in filters:
                if status.get("annotator_id") != filters["annotator_id"]:
                    continue
            if "domain" in filters:
                if status.get("domain") != filters["domain"]:
                    continue
            if "status" in filters:
                if status.get("status") != filters["status"]:
                    continue
            filtered.append(status)

        return filtered

    def get_worker_status(self, annotator_id: int, domain: str) -> Dict[str, Any]:
        """Get detailed status of specific worker."""
        return self.worker_manager.get_worker_status(annotator_id, domain)

    def check_health(self) -> Dict[str, Any]:
        """Detect crashed/stalled workers."""
        all_statuses = self.worker_manager.get_all_statuses()

        crashed = []
        stalled = []
        healthy = 0

        # Calculate average speed
        speeds = [s.get("progress", {}).get("speed", 0.0) for s in all_statuses]
        speeds = [s for s in speeds if s > 0]
        avg_speed = sum(speeds) / len(speeds) if speeds else 1.0

        for status in all_statuses:
            annotator_id = status.get("annotator_id")
            domain = status.get("domain")
            is_stale = status.get("stale", False)
            speed = status.get("progress", {}).get("speed", 0.0)

            # Crashed workers
            if is_stale and status.get("status") == "running":
                crashed.append({
                    "annotator_id": annotator_id,
                    "domain": domain,
                    "last_update": status.get("last_updated", "unknown"),
                    "stale_minutes": 5  # From settings
                })
            # Stalled workers
            elif speed > 0 and speed < avg_speed * 0.5:
                stalled.append({
                    "annotator_id": annotator_id,
                    "domain": domain,
                    "speed": speed,
                    "expected_speed": avg_speed
                })
            else:
                healthy += 1

        return {
            "crashed": crashed,
            "stalled": stalled,
            "healthy": healthy
        }

    def get_quota_status(self) -> Dict[str, Dict[str, Any]]:
        """Get API quota usage estimates."""
        result = {}

        for annotator_id in [1, 2, 3, 4, 5]:
            # Count requests today
            requests_today = 0

            for domain in self.domains:
                progress_path = self.base_dir / "data" / "annotations" / f"annotator_{annotator_id}" / domain / "progress.json"
                if progress_path.exists():
                    progress = atomic_read_json(str(progress_path))
                    if progress:
                        requests_today += len(progress.get("completed_ids", []))

            quota_limit = 1500
            percentage_used = (requests_today / quota_limit * 100) if quota_limit > 0 else 0

            # Estimate depletion (simplified)
            est_depletion = "N/A"

            result[f"annotator_{annotator_id}"] = {
                "requests_today": requests_today,
                "quota_limit": quota_limit,
                "percentage_used": round(percentage_used, 1),
                "estimated_depletion": est_depletion
            }

        return result
