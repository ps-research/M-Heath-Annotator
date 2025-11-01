"""
Worker watchdog for automatic crash detection and recovery.

Monitors all workers and automatically restarts crashed/stuck workers.
Runs as a background task in the FastAPI application.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime, timezone
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.worker_manager import WorkerManager
from backend.core.process_registry import ProcessRegistry
from backend.core.heartbeat_manager import HeartbeatManager
from backend.utils.file_operations import atomic_read_json

logger = logging.getLogger(__name__)


class WorkerWatchdog:
    """
    Monitors workers and automatically restarts crashed ones.

    Features:
    - Detects crashed workers (process died)
    - Detects stuck workers (no heartbeat)
    - Detects orphaned workers (registered but not running)
    - Automatically restarts enabled workers
    - Configurable restart policies
    """

    def __init__(self, check_interval: int = 60, max_restart_attempts: int = 3):
        """
        Initialize worker watchdog.

        Args:
            check_interval: How often to check workers (seconds)
            max_restart_attempts: Max restart attempts before giving up
        """
        self.check_interval = check_interval
        self.max_restart_attempts = max_restart_attempts

        self.worker_manager = WorkerManager()
        self.process_registry = ProcessRegistry()
        self.heartbeat_manager = HeartbeatManager()

        self.base_dir = Path(__file__).parent.parent.parent

        # Track restart attempts: (annotator_id, domain) -> count
        self.restart_attempts: Dict[tuple, int] = {}

        # Track workers that shouldn't be restarted
        self.blacklist: Set[tuple] = set()

        self.running = False

    def _load_settings(self) -> Dict:
        """Load settings configuration."""
        settings_path = self.base_dir / "config" / "settings.json"
        return atomic_read_json(str(settings_path)) or {}

    def _is_enabled(self, annotator_id: int, domain: str) -> bool:
        """Check if worker is enabled in settings."""
        settings = self._load_settings()

        try:
            annotator_settings = settings["annotators"][str(annotator_id)]
            domain_settings = annotator_settings[domain]
            return domain_settings.get("enabled", False)
        except (KeyError, TypeError):
            return False

    def _should_auto_restart(self, annotator_id: int, domain: str) -> bool:
        """
        Check if worker should be automatically restarted.

        Args:
            annotator_id: Annotator ID
            domain: Domain name

        Returns:
            True if should restart
        """
        key = (annotator_id, domain)

        # Check blacklist
        if key in self.blacklist:
            logger.info(f"Worker {annotator_id}/{domain} is blacklisted, not restarting")
            return False

        # Check if enabled
        if not self._is_enabled(annotator_id, domain):
            logger.info(f"Worker {annotator_id}/{domain} is disabled, not restarting")
            return False

        # Check restart attempts
        attempts = self.restart_attempts.get(key, 0)
        if attempts >= self.max_restart_attempts:
            logger.warning(
                f"Worker {annotator_id}/{domain} has exceeded max restart attempts "
                f"({self.max_restart_attempts}), adding to blacklist"
            )
            self.blacklist.add(key)
            return False

        return True

    def _increment_restart_attempt(self, annotator_id: int, domain: str) -> None:
        """Increment restart attempt counter."""
        key = (annotator_id, domain)
        self.restart_attempts[key] = self.restart_attempts.get(key, 0) + 1

    def _reset_restart_attempts(self, annotator_id: int, domain: str) -> None:
        """Reset restart attempt counter."""
        key = (annotator_id, domain)
        if key in self.restart_attempts:
            del self.restart_attempts[key]

    async def check_crashed_workers(self) -> List[Dict]:
        """
        Detect crashed workers (process died).

        Returns:
            List of crashed worker info
        """
        crashed = []

        # Get all registered workers
        registered_workers = self.process_registry.get_all_workers()

        for worker_data in registered_workers:
            annotator_id = worker_data["annotator_id"]
            domain = worker_data["domain"]
            pid = worker_data["pid"]

            # Check if process is actually running
            if not self.process_registry.is_process_running(pid, annotator_id, domain):
                logger.warning(f"Detected crashed worker: {annotator_id}/{domain} (PID {pid})")

                crashed.append({
                    "annotator_id": annotator_id,
                    "domain": domain,
                    "pid": pid,
                    "reason": "process_died"
                })

        return crashed

    async def check_stuck_workers(self) -> List[Dict]:
        """
        Detect stuck workers (no recent heartbeat).

        Returns:
            List of stuck worker info
        """
        stuck_workers = self.heartbeat_manager.get_stuck_workers()

        for worker in stuck_workers:
            logger.warning(
                f"Detected stuck worker: {worker['annotator_id']}/{worker['domain']} "
                f"(last heartbeat {worker['age_seconds']:.0f}s ago)"
            )

        return stuck_workers

    async def check_orphaned_workers(self) -> List[tuple]:
        """
        Detect orphaned workers (registered but not actually running).

        Returns:
            List of (annotator_id, domain) tuples
        """
        orphaned = self.process_registry.get_orphaned_workers()

        if orphaned:
            logger.info(f"Found {len(orphaned)} orphaned worker registrations")

        return orphaned

    async def restart_worker(self, annotator_id: int, domain: str, reason: str) -> bool:
        """
        Attempt to restart a worker.

        Args:
            annotator_id: Annotator ID
            domain: Domain name
            reason: Reason for restart

        Returns:
            True if restart succeeded
        """
        logger.info(f"Attempting to restart worker {annotator_id}/{domain} (reason: {reason})")

        # Check if should restart
        if not self._should_auto_restart(annotator_id, domain):
            return False

        # Increment attempt counter
        self._increment_restart_attempt(annotator_id, domain)

        # Stop worker first (cleanup any remaining resources)
        try:
            await asyncio.to_thread(
                self.worker_manager.stop_worker,
                annotator_id,
                domain,
                timeout=10
            )
        except Exception as e:
            logger.warning(f"Error stopping worker before restart: {e}")

        # Cleanup registry and heartbeat
        self.process_registry.unregister_worker(annotator_id, domain)
        self.heartbeat_manager.cleanup_heartbeat(annotator_id, domain)

        # Wait a bit before restarting
        await asyncio.sleep(2)

        # Start worker
        try:
            result = await asyncio.to_thread(
                self.worker_manager.start_worker,
                annotator_id,
                domain
            )

            if result["status"] == "started":
                logger.info(f"✅ Successfully restarted worker {annotator_id}/{domain}")
                # Reset restart attempts on successful start
                await asyncio.sleep(30)  # Wait to verify it stays running
                if self.process_registry.is_worker_actually_running(annotator_id, domain):
                    self._reset_restart_attempts(annotator_id, domain)
                return True
            else:
                logger.error(f"❌ Failed to restart worker {annotator_id}/{domain}: {result}")
                return False

        except Exception as e:
            logger.error(f"❌ Exception restarting worker {annotator_id}/{domain}: {e}")
            return False

    async def cleanup_orphaned_registrations(self) -> int:
        """
        Remove registry entries for dead workers.

        Returns:
            Number of entries cleaned up
        """
        cleaned = self.process_registry.cleanup_dead_workers()
        if cleaned:
            logger.info(f"Cleaned up {len(cleaned)} orphaned worker registrations")
        return len(cleaned)

    async def check_and_recover(self) -> Dict[str, int]:
        """
        Check all workers and attempt recovery.

        Returns:
            Statistics dictionary
        """
        stats = {
            "checked": 0,
            "crashed": 0,
            "stuck": 0,
            "restarted": 0,
            "failed_restarts": 0,
            "orphaned_cleaned": 0
        }

        # Cleanup orphaned registrations first
        stats["orphaned_cleaned"] = await self.cleanup_orphaned_registrations()

        # Check for crashed workers
        crashed_workers = await self.check_crashed_workers()
        stats["crashed"] = len(crashed_workers)

        # Check for stuck workers
        stuck_workers = await self.check_stuck_workers()
        stats["stuck"] = len(stuck_workers)

        # Combine crashed and stuck for restart attempts
        workers_to_restart = []

        for worker in crashed_workers:
            workers_to_restart.append((
                worker["annotator_id"],
                worker["domain"],
                worker["reason"]
            ))

        for worker in stuck_workers:
            workers_to_restart.append((
                worker["annotator_id"],
                worker["domain"],
                "stuck_no_heartbeat"
            ))

        # Attempt restarts
        for annotator_id, domain, reason in workers_to_restart:
            success = await self.restart_worker(annotator_id, domain, reason)
            if success:
                stats["restarted"] += 1
            else:
                stats["failed_restarts"] += 1

        stats["checked"] = len(self.process_registry.get_all_workers())

        return stats

    async def monitor_loop(self) -> None:
        """
        Main monitoring loop.

        Runs continuously in background, checking workers periodically.
        """
        self.running = True
        logger.info(f"🔍 Worker Watchdog started (check interval: {self.check_interval}s)")

        iteration = 0

        while self.running:
            try:
                iteration += 1
                logger.debug(f"Watchdog check iteration {iteration}")

                # Run check and recovery
                stats = await self.check_and_recover()

                # Log statistics if anything interesting happened
                if stats["crashed"] > 0 or stats["stuck"] > 0 or stats["restarted"] > 0:
                    logger.info(
                        f"Watchdog stats: checked={stats['checked']}, "
                        f"crashed={stats['crashed']}, stuck={stats['stuck']}, "
                        f"restarted={stats['restarted']}, failed={stats['failed_restarts']}, "
                        f"orphaned_cleaned={stats['orphaned_cleaned']}"
                    )

            except Exception as e:
                logger.error(f"Error in watchdog monitor loop: {e}", exc_info=True)

            # Wait before next check
            await asyncio.sleep(self.check_interval)

    async def stop(self) -> None:
        """Stop the watchdog."""
        logger.info("Stopping Worker Watchdog...")
        self.running = False

    def reset_blacklist(self) -> None:
        """Clear the restart blacklist."""
        self.blacklist.clear()
        self.restart_attempts.clear()
        logger.info("Watchdog blacklist cleared")

    def add_to_blacklist(self, annotator_id: int, domain: str) -> None:
        """
        Manually add worker to blacklist.

        Args:
            annotator_id: Annotator ID
            domain: Domain name
        """
        key = (annotator_id, domain)
        self.blacklist.add(key)
        logger.info(f"Added worker {annotator_id}/{domain} to blacklist")

    def remove_from_blacklist(self, annotator_id: int, domain: str) -> None:
        """
        Remove worker from blacklist.

        Args:
            annotator_id: Annotator ID
            domain: Domain name
        """
        key = (annotator_id, domain)
        if key in self.blacklist:
            self.blacklist.discard(key)
            logger.info(f"Removed worker {annotator_id}/{domain} from blacklist")
