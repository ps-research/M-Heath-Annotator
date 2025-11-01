"""
Heartbeat system for worker health monitoring.

Workers send periodic heartbeats independent of annotation progress,
allowing detection of stuck/frozen workers even if they're not completing samples.
"""

import os
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.utils.file_operations import atomic_read_json, atomic_write_json, ensure_directory


class HeartbeatManager:
    """
    Manages worker heartbeats for health monitoring.

    Workers send heartbeats every 30 seconds.
    If no heartbeat for 2 minutes, worker is considered stuck/dead.
    """

    def __init__(self):
        """Initialize heartbeat manager."""
        self.base_dir = Path(__file__).parent.parent.parent
        self.heartbeat_dir = self.base_dir / "data" / "heartbeats"
        ensure_directory(str(self.heartbeat_dir))
        self.heartbeat_timeout = 120  # 2 minutes

    def _get_heartbeat_path(self, annotator_id: int, domain: str) -> Path:
        """Get path to heartbeat file."""
        return self.heartbeat_dir / f"annotator_{annotator_id}_{domain}.json"

    def send_heartbeat(self, annotator_id: int, domain: str, iteration: int = 0, status: str = "running") -> None:
        """
        Send heartbeat from worker.

        Args:
            annotator_id: Annotator ID
            domain: Domain name
            iteration: Current iteration count
            status: Current worker status
        """
        heartbeat_path = self._get_heartbeat_path(annotator_id, domain)

        heartbeat_data = {
            "annotator_id": annotator_id,
            "domain": domain,
            "pid": os.getpid(),
            "last_heartbeat": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "iteration": iteration,
            "status": status
        }

        atomic_write_json(heartbeat_data, str(heartbeat_path))

    def get_heartbeat(self, annotator_id: int, domain: str) -> Optional[Dict]:
        """
        Get heartbeat data for a worker.

        Args:
            annotator_id: Annotator ID
            domain: Domain name

        Returns:
            Heartbeat data dict or None if no heartbeat file
        """
        heartbeat_path = self._get_heartbeat_path(annotator_id, domain)

        if not heartbeat_path.exists():
            return None

        return atomic_read_json(str(heartbeat_path))

    def is_heartbeat_alive(self, annotator_id: int, domain: str) -> bool:
        """
        Check if worker heartbeat is recent.

        Args:
            annotator_id: Annotator ID
            domain: Domain name

        Returns:
            True if heartbeat is recent (within timeout)
        """
        heartbeat = self.get_heartbeat(annotator_id, domain)

        if heartbeat is None:
            return False

        last_heartbeat_str = heartbeat.get("last_heartbeat")
        if not last_heartbeat_str:
            return False

        try:
            last_heartbeat = datetime.fromisoformat(last_heartbeat_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            elapsed = (now - last_heartbeat).total_seconds()

            return elapsed < self.heartbeat_timeout

        except Exception:
            return False

    def get_heartbeat_age(self, annotator_id: int, domain: str) -> Optional[float]:
        """
        Get age of last heartbeat in seconds.

        Args:
            annotator_id: Annotator ID
            domain: Domain name

        Returns:
            Age in seconds, or None if no heartbeat
        """
        heartbeat = self.get_heartbeat(annotator_id, domain)

        if heartbeat is None:
            return None

        last_heartbeat_str = heartbeat.get("last_heartbeat")
        if not last_heartbeat_str:
            return None

        try:
            last_heartbeat = datetime.fromisoformat(last_heartbeat_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            return (now - last_heartbeat).total_seconds()

        except Exception:
            return None

    def cleanup_heartbeat(self, annotator_id: int, domain: str) -> None:
        """
        Remove heartbeat file for a worker.

        Args:
            annotator_id: Annotator ID
            domain: Domain name
        """
        heartbeat_path = self._get_heartbeat_path(annotator_id, domain)

        try:
            if heartbeat_path.exists():
                heartbeat_path.unlink()
        except Exception:
            pass

    def get_all_heartbeats(self) -> List[Dict]:
        """
        Get all heartbeats.

        Returns:
            List of heartbeat data dictionaries
        """
        heartbeats = []

        for heartbeat_file in self.heartbeat_dir.glob("annotator_*.json"):
            data = atomic_read_json(str(heartbeat_file))
            if data:
                heartbeats.append(data)

        return heartbeats

    def get_stuck_workers(self) -> List[Dict]:
        """
        Find workers with stale heartbeats (likely stuck).

        Returns:
            List of worker info for stuck workers
        """
        stuck = []

        for heartbeat_file in self.heartbeat_dir.glob("annotator_*.json"):
            data = atomic_read_json(str(heartbeat_file))
            if not data:
                continue

            annotator_id = data.get("annotator_id")
            domain = data.get("domain")

            if not self.is_heartbeat_alive(annotator_id, domain):
                age = self.get_heartbeat_age(annotator_id, domain)
                stuck.append({
                    "annotator_id": annotator_id,
                    "domain": domain,
                    "pid": data.get("pid"),
                    "last_heartbeat": data.get("last_heartbeat"),
                    "age_seconds": age,
                    "status": data.get("status")
                })

        return stuck

    def cleanup_all_heartbeats(self) -> int:
        """
        Remove all heartbeat files.

        Returns:
            Number of files removed
        """
        count = 0
        for heartbeat_file in self.heartbeat_dir.glob("annotator_*.json"):
            try:
                heartbeat_file.unlink()
                count += 1
            except Exception:
                pass

        return count


class WorkerHeartbeat:
    """
    Helper class for workers to easily send heartbeats.

    Usage in worker:
        heartbeat = WorkerHeartbeat(annotator_id, domain)
        heartbeat.start()  # Send initial heartbeat

        # In main loop:
        heartbeat.maybe_send()  # Sends if interval elapsed
    """

    def __init__(self, annotator_id: int, domain: str, interval: int = 30):
        """
        Initialize worker heartbeat helper.

        Args:
            annotator_id: Annotator ID
            domain: Domain name
            interval: Heartbeat interval in seconds
        """
        self.annotator_id = annotator_id
        self.domain = domain
        self.interval = interval
        self.manager = HeartbeatManager()
        self.last_heartbeat_time = 0
        self.iteration = 0

    def start(self) -> None:
        """Send initial heartbeat."""
        self.send_now()

    def send_now(self, status: str = "running") -> None:
        """
        Send heartbeat immediately.

        Args:
            status: Current worker status
        """
        self.manager.send_heartbeat(
            self.annotator_id,
            self.domain,
            self.iteration,
            status
        )
        self.last_heartbeat_time = time.time()

    def maybe_send(self, status: str = "running") -> bool:
        """
        Send heartbeat if interval has elapsed.

        Args:
            status: Current worker status

        Returns:
            True if heartbeat was sent
        """
        elapsed = time.time() - self.last_heartbeat_time

        if elapsed >= self.interval:
            self.send_now(status)
            return True

        return False

    def increment_iteration(self) -> None:
        """Increment iteration counter."""
        self.iteration += 1

    def cleanup(self) -> None:
        """Remove heartbeat file on shutdown."""
        self.manager.cleanup_heartbeat(self.annotator_id, self.domain)
