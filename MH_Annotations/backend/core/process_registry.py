"""
Persistent process registry for tracking worker processes across backend restarts.

This module provides robust process tracking that survives backend restarts
and accurately detects running workers using the /proc filesystem.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, List, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.utils.file_operations import atomic_read_json, atomic_write_json, ensure_directory


class ProcessRegistry:
    """
    Persistent registry for tracking worker processes.

    Provides:
    - Persistent storage that survives backend restarts
    - Accurate PID validation using /proc filesystem
    - Orphan detection and cleanup
    - Prevention of duplicate workers
    """

    def __init__(self):
        """Initialize process registry."""
        self.base_dir = Path(__file__).parent.parent.parent
        self.registry_dir = self.base_dir / "data" / "process_registry"
        ensure_directory(str(self.registry_dir))
        self.registry_path = self.registry_dir / "workers.json"

    def _load(self) -> Dict[str, Dict]:
        """Load registry from disk."""
        data = atomic_read_json(str(self.registry_path))
        if data is None:
            return {}
        return data

    def _save(self, registry: Dict[str, Dict]) -> None:
        """Save registry to disk."""
        atomic_write_json(registry, str(self.registry_path))

    def _make_key(self, annotator_id: int, domain: str) -> str:
        """Generate registry key."""
        return f"{annotator_id}_{domain}"

    def is_process_running(self, pid: int, annotator_id: int, domain: str) -> bool:
        """
        Check if process is actually running and is the correct worker.

        Uses /proc filesystem for accurate detection, checking:
        1. Process exists
        2. Command line contains worker.py
        3. Command line contains correct annotator and domain

        Args:
            pid: Process ID to check
            annotator_id: Expected annotator ID
            domain: Expected domain

        Returns:
            True if process is running and is the correct worker
        """
        if pid is None or pid <= 0:
            return False

        try:
            # Method 1: Check /proc/PID/cmdline (Linux-specific but most reliable)
            cmdline_path = Path(f"/proc/{pid}/cmdline")
            if cmdline_path.exists():
                # Read command line (null-separated)
                cmdline = cmdline_path.read_text().replace('\x00', ' ')

                # Verify it's a worker process with correct parameters
                is_worker = (
                    "worker.py" in cmdline and
                    f"--annotator {annotator_id}" in cmdline and
                    f"--domain {domain}" in cmdline
                )
                return is_worker

        except (FileNotFoundError, PermissionError, ProcessLookupError):
            pass

        # Method 2: Fallback to os.kill check (less reliable)
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def register_worker(self, annotator_id: int, domain: str, pid: int) -> None:
        """
        Register a worker process.

        Args:
            annotator_id: Annotator ID
            domain: Domain name
            pid: Process ID
        """
        registry = self._load()
        key = self._make_key(annotator_id, domain)

        registry[key] = {
            "annotator_id": annotator_id,
            "domain": domain,
            "pid": pid,
            "started_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "last_check": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "status": "running"
        }

        self._save(registry)

    def unregister_worker(self, annotator_id: int, domain: str) -> None:
        """
        Unregister a worker process.

        Args:
            annotator_id: Annotator ID
            domain: Domain name
        """
        registry = self._load()
        key = self._make_key(annotator_id, domain)

        if key in registry:
            del registry[key]
            self._save(registry)

    def get_worker_pid(self, annotator_id: int, domain: str) -> Optional[int]:
        """
        Get PID for a worker.

        Args:
            annotator_id: Annotator ID
            domain: Domain name

        Returns:
            PID if worker is registered, None otherwise
        """
        registry = self._load()
        key = self._make_key(annotator_id, domain)

        if key in registry:
            return registry[key].get("pid")
        return None

    def is_worker_registered(self, annotator_id: int, domain: str) -> bool:
        """
        Check if worker is registered.

        Args:
            annotator_id: Annotator ID
            domain: Domain name

        Returns:
            True if worker is registered
        """
        registry = self._load()
        key = self._make_key(annotator_id, domain)
        return key in registry

    def is_worker_actually_running(self, annotator_id: int, domain: str) -> bool:
        """
        Check if worker is registered AND actually running.

        Args:
            annotator_id: Annotator ID
            domain: Domain name

        Returns:
            True if worker is running
        """
        pid = self.get_worker_pid(annotator_id, domain)
        if pid is None:
            return False

        return self.is_process_running(pid, annotator_id, domain)

    def cleanup_dead_workers(self) -> List[Tuple[int, str]]:
        """
        Remove registry entries for dead processes.

        Returns:
            List of (annotator_id, domain) tuples for cleaned up workers
        """
        registry = self._load()
        cleaned_up = []

        for key, data in list(registry.items()):
            annotator_id = data["annotator_id"]
            domain = data["domain"]
            pid = data["pid"]

            if not self.is_process_running(pid, annotator_id, domain):
                del registry[key]
                cleaned_up.append((annotator_id, domain))

        if cleaned_up:
            self._save(registry)

        return cleaned_up

    def get_all_workers(self) -> List[Dict]:
        """
        Get all registered workers.

        Returns:
            List of worker info dictionaries
        """
        registry = self._load()
        return list(registry.values())

    def get_running_workers(self) -> List[Dict]:
        """
        Get all workers that are actually running.

        Returns:
            List of worker info dictionaries for running workers
        """
        registry = self._load()
        running = []

        for data in registry.values():
            annotator_id = data["annotator_id"]
            domain = data["domain"]
            pid = data["pid"]

            if self.is_process_running(pid, annotator_id, domain):
                running.append(data)

        return running

    def get_orphaned_workers(self) -> List[Tuple[int, str]]:
        """
        Find workers that are registered but not actually running.

        Returns:
            List of (annotator_id, domain) tuples for orphaned workers
        """
        registry = self._load()
        orphaned = []

        for key, data in registry.items():
            annotator_id = data["annotator_id"]
            domain = data["domain"]
            pid = data["pid"]

            if not self.is_process_running(pid, annotator_id, domain):
                orphaned.append((annotator_id, domain))

        return orphaned

    def update_last_check(self, annotator_id: int, domain: str) -> None:
        """
        Update last check timestamp for a worker.

        Args:
            annotator_id: Annotator ID
            domain: Domain name
        """
        registry = self._load()
        key = self._make_key(annotator_id, domain)

        if key in registry:
            registry[key]["last_check"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            self._save(registry)
