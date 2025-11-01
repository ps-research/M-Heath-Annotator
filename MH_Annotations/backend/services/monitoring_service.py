"""
Monitoring and status aggregation service.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.worker_manager import WorkerManager
from backend.core.db_manager import get_db
from backend.utils.file_operations import atomic_read_json


class MonitoringService:
    """Service for monitoring system and worker status."""

    def __init__(self):
        """Initialize monitoring service."""
        self.worker_manager = WorkerManager()
        self.db = get_db()
        self.base_dir = Path(__file__).parent.parent.parent
        self.domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]

    def get_system_overview(self) -> Dict[str, Any]:
        """Get high-level system statistics from database."""
        return self.db.get_system_overview()

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
        """Detect crashed/stalled workers using database."""
        # Get stuck workers from database (heartbeat-based)
        stuck_workers = self.db.get_stuck_workers()

        crashed = []
        for worker in stuck_workers:
            crashed.append({
                "annotator_id": worker['annotator_id'],
                "domain": worker['domain'],
                "last_heartbeat": worker.get('heartbeat_time', 'unknown'),
                "minutes_ago": round(worker.get('minutes_ago', 0), 2)
            })

        # Get all statuses for stalled detection
        all_statuses = self.worker_manager.get_all_statuses()

        stalled = []
        healthy = 0

        # Calculate average speed
        speeds = [s.get("progress", {}).get("speed", 0.0) for s in all_statuses if s.get("status") == "running"]
        speeds = [s for s in speeds if s > 0]
        avg_speed = sum(speeds) / len(speeds) if speeds else 1.0

        for status in all_statuses:
            if status.get("status") != "running":
                continue

            annotator_id = status.get("annotator_id")
            domain = status.get("domain")
            speed = status.get("progress", {}).get("speed", 0.0)

            # Stalled workers (running but slow)
            if speed > 0 and speed < avg_speed * 0.5:
                stalled.append({
                    "annotator_id": annotator_id,
                    "domain": domain,
                    "speed": speed,
                    "expected_speed": round(avg_speed, 2)
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
