"""
Worker manager for spawning and controlling worker processes.

UPGRADED: Now uses ProcessRegistry for persistent tracking and concurrency limits.
"""

import sys
import os
import signal
import subprocess
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.db_manager import get_db
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

        # Use database manager (replaces ProcessRegistry, HeartbeatManager, ProgressLogger)
        self.db = get_db()

        # Track running processes: (annotator_id, domain) -> subprocess.Popen
        self.processes: Dict[Tuple[int, str], subprocess.Popen] = {}

        # Concurrency limit
        self.max_concurrent_workers = max_concurrent_workers

        # Load settings
        settings_path = self.base_dir / "config" / "settings.json"
        self.settings = atomic_read_json(str(settings_path))

        if not self.settings:
            raise FileNotFoundError(f"Settings file not found: {settings_path}")

        # Initialize database with worker configurations
        self.db.initialize_workers(self.settings)

        self.logger.info("WorkerManager initialized")

        # Sync with running workers from database (after restart)
        self._sync_processes_from_database()

    def _sync_processes_from_database(self) -> None:
        """
        Sync in-memory processes dict with database.

        Called on startup to detect workers that were running before backend restart.
        Note: We cannot recreate subprocess.Popen objects, but we log their existence.
        """
        running = self.db.get_all_running_workers()
        if running:
            self.logger.warning(
                f"Found {len(running)} workers running from before backend restart. "
                "These will be managed via database and control signals."
            )
            for worker_info in running:
                ann_id = worker_info['annotator_id']
                domain = worker_info['domain']
                pid = worker_info['pid']
                self.logger.info(f"  - Worker {ann_id}/{domain} (PID {pid})")

    def start_worker(self, annotator_id: int, domain: str) -> Dict[str, Any]:
        """
        Start a worker process.

        Args:
            annotator_id: Annotator ID (1-5)
            domain: Domain name

        Returns:
            Status dictionary with result
        """
        # Check if already running using database
        status = self.db.get_worker_status(annotator_id, domain)
        if status.get('running'):
            pid = status.get('pid')
            self.logger.warning(f"Worker {annotator_id}/{domain} already running (PID {pid})")
            return {
                "status": "already_running",
                "pid": pid,
                "annotator_id": annotator_id,
                "domain": domain
            }

        # Check concurrency limit
        running_count = len(self.db.get_all_running_workers())
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

            # Store process
            key = (annotator_id, domain)
            self.processes[key] = proc

            # Register in database
            self.db.register_worker_process(annotator_id, domain, proc.pid)

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

        FIXED: Now handles workers running from before backend restart by using ProcessRegistry.

        Args:
            annotator_id: Annotator ID
            domain: Domain name
            timeout: Seconds to wait before forcing kill

        Returns:
            Status dictionary
        """
        key = (annotator_id, domain)

        # Check database for worker PID
        status = self.db.get_worker_status(annotator_id, domain)
        pid = status.get('pid')

        # Check if worker is actually running
        is_running = status.get('running', False)

        if not pid or not is_running:
            # Cleanup if needed
            if pid:
                self.db.unregister_worker_process(annotator_id, domain)

            return {
                "status": "not_running",
                "annotator_id": annotator_id,
                "domain": domain
            }

        # Get subprocess from in-memory dict if available
        proc = self.processes.get(key)

        # Send stop signal via control file
        control_path = self.base_dir / "control" / f"annotator_{annotator_id}_{domain}.json"

        control_data = {
            "command": "stop",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }

        atomic_write_json(control_data, str(control_path))

        print(f"⏹️  Sent stop signal to Annotator {annotator_id}, Domain {domain} (PID {pid})")
        print(f"   Waiting up to {timeout} seconds for graceful exit...")

        exit_code = 0
        forced = False

        # FIXED: Handle both cases - with and without subprocess object
        if proc is not None:
            # We have the subprocess object - use it normally
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

            # Cleanup in-memory reference
            if key in self.processes:
                del self.processes[key]

        else:
            # Backend was restarted - use PID directly
            print(f"   (Backend restarted - managing via PID)")
            timeout_end = time.time() + timeout

            # Wait for process to exit by monitoring PID
            while time.time() < timeout_end:
                if not self.process_registry.is_process_running(pid, annotator_id, domain):
                    print(f"✅ Worker exited gracefully")
                    forced = False
                    break
                time.sleep(1)
            else:
                # Timeout - force kill using signal
                print(f"⚠️  Worker did not exit gracefully, forcing kill...")
                try:
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(2)  # Give it time to die
                    exit_code = -9
                    forced = True
                    print(f"✅ Worker killed")
                except ProcessLookupError:
                    # Already dead
                    print(f"✅ Worker already stopped")
                    pass

        # Cleanup database registry and heartbeat
        self.db.unregister_worker_process(annotator_id, domain)
        self.db.cleanup_heartbeat(annotator_id, domain)

        # Delete control file
        try:
            if control_path.exists():
                control_path.unlink()
        except:
            pass

        self.logger.info(f"Worker {annotator_id}/{domain} stopped (pid={pid}, exit_code={exit_code}, forced={forced})")

        return {
            "status": "stopped",
            "annotator_id": annotator_id,
            "domain": domain,
            "pid": pid,
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
        # Get status from database
        return self.db.get_worker_status(annotator_id, domain)

    def get_all_statuses(self) -> List[Dict[str, Any]]:
        """
        Get status of all annotator-domain pairs.

        Returns:
            List of status dictionaries
        """
        # Get all statuses from database in one call
        return self.db.get_all_worker_statuses()

    def stop_all_workers(self, timeout: int = 30) -> Dict[str, Any]:
        """
        Stop all running workers.

        FIXED: Now uses ProcessRegistry instead of in-memory dict.
        This ensures "Terminate All" works even after backend restart.

        Args:
            timeout: Timeout per worker

        Returns:
            Summary dictionary
        """
        print(f"\n⏹️  Stopping all workers...\n")

        # Get running workers from database
        running_workers = self.db.get_all_running_workers()

        if not running_workers:
            print("ℹ️  No workers currently running")
            self.logger.info("stop_all_workers: No workers running")
            return {"stopped": 0, "forced": 0}

        self.logger.info(f"Stopping {len(running_workers)} running workers")

        stopped_count = 0
        forced_count = 0

        for worker_info in running_workers:
            annotator_id = worker_info['annotator_id']
            domain = worker_info['domain']
            pid = worker_info['pid']

            print(f"Stopping worker {annotator_id}/{domain} (PID {pid})...")

            result = self.stop_worker(annotator_id, domain, timeout)

            if result["status"] in ["stopped", "already_stopped"]:
                stopped_count += 1
                if result.get("forced", False):
                    forced_count += 1

        print(f"\n✅ Stopped {stopped_count} workers (forced: {forced_count})\n")
        self.logger.info(f"Stopped {stopped_count} workers (forced: {forced_count})")

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
