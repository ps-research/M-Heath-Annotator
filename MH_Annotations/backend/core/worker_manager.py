"""
Worker manager for spawning and controlling worker processes.

UPGRADED: Now uses ProcessRegistry for persistent tracking and concurrency limits.
"""

import sys
import os
import subprocess
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.progress_logger import ProgressLogger
from backend.core.process_registry import ProcessRegistry
from backend.core.heartbeat_manager import HeartbeatManager
from backend.core.logger_config import get_manager_logger
from backend.utils.file_operations import atomic_read_json, atomic_write_json


class WorkerManager:
    """
    Manages worker processes for annotation.

    Handles:
    - Spawning worker subprocesses
    - Sending control signals
    - Monitoring worker status
    - Graceful shutdown
    """

    def __init__(self, max_concurrent_workers: int = 10):
        """
        Initialize worker manager.

        Args:
            max_concurrent_workers: Maximum number of workers to run concurrently
        """
        self.base_dir = Path(__file__).parent.parent.parent
        self.logger = get_manager_logger()

        # NEW: Use ProcessRegistry instead of in-memory dict
        self.process_registry = ProcessRegistry()
        self.heartbeat_manager = HeartbeatManager()

        # Track running processes: (annotator_id, domain) -> subprocess.Popen
        # Keep for backward compatibility during transition
        self.processes: Dict[Tuple[int, str], subprocess.Popen] = {}

        # NEW: Concurrency limit
        self.max_concurrent_workers = max_concurrent_workers

        # Load settings
        settings_path = self.base_dir / "config" / "settings.json"
        self.settings = atomic_read_json(str(settings_path))

        if not self.settings:
            raise FileNotFoundError(f"Settings file not found: {settings_path}")

        self.logger.info("WorkerManager initialized")

    def start_worker(self, annotator_id: int, domain: str) -> Dict[str, Any]:
        """
        Start a worker process.

        Args:
            annotator_id: Annotator ID (1-5)
            domain: Domain name

        Returns:
            Status dictionary with result
        """
        # NEW: Check if already running using ProcessRegistry
        if self.process_registry.is_worker_actually_running(annotator_id, domain):
            pid = self.process_registry.get_worker_pid(annotator_id, domain)
            self.logger.warning(f"Worker {annotator_id}/{domain} already running (PID {pid})")
            return {
                "status": "already_running",
                "pid": pid,
                "annotator_id": annotator_id,
                "domain": domain
            }

        # Check concurrency limit
        running_count = len(self.process_registry.get_running_workers())
        if running_count >= self.max_concurrent_workers:
            self.logger.warning(
                f"Cannot start worker {annotator_id}/{domain}: "
                f"concurrent limit reached ({running_count}/{self.max_concurrent_workers})"
            )
            return {
                "status": "concurrency_limit_reached",
                "annotator_id": annotator_id,
                "domain": domain,
                "message": f"Max concurrent workers ({self.max_concurrent_workers}) reached"
            }

        # Check if enabled in settings
        try:
            annotator_settings = self.settings["annotators"][str(annotator_id)]
            domain_settings = annotator_settings[domain]

            if not domain_settings.get("enabled", False):
                return {
                    "status": "disabled",
                    "annotator_id": annotator_id,
                    "domain": domain,
                    "message": "This annotator-domain pair is disabled in settings"
                }
        except (KeyError, TypeError):
            return {
                "status": "disabled",
                "annotator_id": annotator_id,
                "domain": domain,
                "message": "Configuration not found for this annotator-domain pair"
            }

        # Build command
        worker_script = self.base_dir / "backend" / "core" / "worker.py"

        cmd = [
            sys.executable,  # Python interpreter
            str(worker_script),
            "--annotator", str(annotator_id),
            "--domain", domain
        ]

        try:
            # Spawn subprocess
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.base_dir)  # Set working directory
            )

            # Store process (backward compatibility)
            key = (annotator_id, domain)
            self.processes[key] = proc

            # NEW: Register in ProcessRegistry
            self.process_registry.register_worker(annotator_id, domain, proc.pid)

            self.logger.info(f"Started worker for Annotator {annotator_id}, Domain {domain}, PID: {proc.pid}")

            return {
                "status": "started",
                "pid": proc.pid,
                "annotator_id": annotator_id,
                "domain": domain
            }

        except Exception as e:
            return {
                "status": "error",
                "annotator_id": annotator_id,
                "domain": domain,
                "message": f"Failed to start worker: {str(e)}"
            }

    def stop_worker(self, annotator_id: int, domain: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Stop a worker process gracefully.

        Args:
            annotator_id: Annotator ID
            domain: Domain name
            timeout: Seconds to wait before forcing kill

        Returns:
            Status dictionary
        """
        key = (annotator_id, domain)

        # Check if running
        if key not in self.processes:
            return {
                "status": "not_running",
                "annotator_id": annotator_id,
                "domain": domain
            }

        proc = self.processes[key]

        # Check if already finished
        if proc.poll() is not None:
            exit_code = proc.returncode
            del self.processes[key]
            return {
                "status": "already_stopped",
                "annotator_id": annotator_id,
                "domain": domain,
                "exit_code": exit_code
            }

        # Send stop signal via control file
        control_path = self.base_dir / "control" / f"annotator_{annotator_id}_{domain}.json"

        control_data = {
            "command": "stop",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }

        atomic_write_json(control_data, str(control_path))

        print(f"⏹️  Sent stop signal to Annotator {annotator_id}, Domain {domain}")
        print(f"   Waiting up to {timeout} seconds for graceful exit...")

        # Wait for graceful exit
        try:
            proc.wait(timeout=timeout)
            exit_code = proc.returncode
            forced = False
            print(f"✅ Worker exited gracefully with code {exit_code}")

        except subprocess.TimeoutExpired:
            # Force kill
            print(f"⚠️  Worker did not exit gracefully, forcing kill...")
            proc.kill()
            proc.wait()
            exit_code = -9
            forced = True
            print(f"✅ Worker killed")

        # Cleanup
        del self.processes[key]

        # NEW: Unregister from ProcessRegistry and cleanup heartbeat
        self.process_registry.unregister_worker(annotator_id, domain)
        self.heartbeat_manager.cleanup_heartbeat(annotator_id, domain)

        # Delete control file
        try:
            if control_path.exists():
                control_path.unlink()
        except:
            pass

        self.logger.info(f"Worker {annotator_id}/{domain} stopped (exit_code={exit_code}, forced={forced})")

        return {
            "status": "stopped",
            "annotator_id": annotator_id,
            "domain": domain,
            "exit_code": exit_code,
            "forced": forced
        }

    def pause_worker(self, annotator_id: int, domain: str) -> Dict[str, Any]:
        """
        Pause a worker process.

        Args:
            annotator_id: Annotator ID
            domain: Domain name

        Returns:
            Status dictionary
        """
        control_path = self.base_dir / "control" / f"annotator_{annotator_id}_{domain}.json"

        control_data = {
            "command": "pause",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }

        atomic_write_json(control_data, str(control_path))

        print(f"⏸️  Sent pause signal to Annotator {annotator_id}, Domain {domain}")

        return {
            "status": "pause_signal_sent",
            "annotator_id": annotator_id,
            "domain": domain
        }

    def resume_worker(self, annotator_id: int, domain: str) -> Dict[str, Any]:
        """
        Resume a paused worker process.

        Args:
            annotator_id: Annotator ID
            domain: Domain name

        Returns:
            Status dictionary
        """
        control_path = self.base_dir / "control" / f"annotator_{annotator_id}_{domain}.json"

        control_data = {
            "command": "resume",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }

        atomic_write_json(control_data, str(control_path))

        print(f"▶️  Sent resume signal to Annotator {annotator_id}, Domain {domain}")

        return {
            "status": "resume_signal_sent",
            "annotator_id": annotator_id,
            "domain": domain
        }

    def get_worker_status(self, annotator_id: int, domain: str) -> Dict[str, Any]:
        """
        Get status of a worker.

        Args:
            annotator_id: Annotator ID
            domain: Domain name

        Returns:
            Status dictionary with comprehensive information
        """
        # Load progress
        try:
            logger = ProgressLogger(annotator_id, domain)
            progress = logger.load()
        except Exception as e:
            return {
                "annotator_id": annotator_id,
                "domain": domain,
                "status": "error",
                "error": str(e)
            }

        # NEW: Use ProcessRegistry for accurate process detection
        pid = progress.get("pid")
        running = self.process_registry.is_worker_actually_running(annotator_id, domain)

        # NEW: Check heartbeat for additional accuracy
        heartbeat_alive = self.heartbeat_manager.is_heartbeat_alive(annotator_id, domain)

        # Check if stale using progress file
        crash_detection_minutes = self.settings["global"]["crash_detection_minutes"]
        progress_stale = logger.is_stale(minutes=crash_detection_minutes)

        # Determine status with enhanced detection
        status = progress.get("status", "unknown")

        # If heartbeat is dead and progress says running, mark as crashed
        if not heartbeat_alive and status == "running" and pid is not None:
            status = "crashed"
            running = False

        # If progress is stale and was running, mark as crashed
        elif progress_stale and status == "running":
            status = "crashed"
            running = False

        # If PID exists but process is not actually running, mark as crashed
        elif pid is not None and not running and status == "running":
            status = "crashed"

        return {
            "annotator_id": annotator_id,
            "domain": domain,
            "status": status,
            "running": running,
            "stale": progress_stale,
            "progress": {
                "completed": len(progress.get("completed_ids", [])),
                "target": progress.get("target_count", 0),
                "malformed": len(progress.get("malformed_ids", [])),
                "speed": progress.get("stats", {}).get("samples_per_min", 0.0)
            },
            "last_updated": progress.get("last_updated", "unknown"),
            "pid": progress.get("pid")
        }

    def get_all_statuses(self) -> List[Dict[str, Any]]:
        """
        Get status of all annotator-domain pairs.

        Returns:
            List of status dictionaries
        """
        statuses = []

        domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]

        for annotator_id in [1, 2, 3, 4, 5]:
            for domain in domains:
                status = self.get_worker_status(annotator_id, domain)
                statuses.append(status)

        return statuses

    def stop_all_workers(self, timeout: int = 30) -> Dict[str, Any]:
        """
        Stop all running workers.

        Args:
            timeout: Timeout per worker

        Returns:
            Summary dictionary
        """
        print(f"\n⏹️  Stopping all workers...\n")

        # Get list of running workers
        running_keys = list(self.processes.keys())

        stopped_count = 0
        forced_count = 0

        for key in running_keys:
            annotator_id, domain = key
            result = self.stop_worker(annotator_id, domain, timeout)

            if result["status"] == "stopped":
                stopped_count += 1
                if result.get("forced", False):
                    forced_count += 1

        print(f"\n✅ Stopped {stopped_count} workers (forced: {forced_count})\n")

        return {
            "stopped": stopped_count,
            "forced": forced_count
        }

    def start_all_enabled(self) -> Dict[str, Any]:
        """
        Start all enabled annotator-domain pairs.

        Returns:
            Summary dictionary
        """
        print(f"\n🚀 Starting all enabled workers...\n")

        domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
        started_count = 0
        failed_count = 0
        disabled_count = 0

        for annotator_id in [1, 2, 3, 4, 5]:
            for domain in domains:
                result = self.start_worker(annotator_id, domain)

                if result["status"] == "started":
                    started_count += 1
                elif result["status"] == "disabled":
                    disabled_count += 1
                elif result["status"] == "error":
                    failed_count += 1
                    print(f"❌ {result.get('message', 'Unknown error')}")

        print(f"\n✅ Started: {started_count} workers")
        print(f"⏭️  Disabled: {disabled_count} workers")
        print(f"❌ Failed: {failed_count} workers\n")

        return {
            "started": started_count,
            "disabled": disabled_count,
            "failed": failed_count
        }
