"""
Database manager for M-Heath Annotator.

Replaces file-based progress tracking with SQLite database.
Handles all worker state, progress tracking, heartbeats, and event logging.
"""

import os
import sqlite3
import threading
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from contextlib import contextmanager
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class DatabaseManager:
    """
    Thread-safe SQLite database manager.

    Replaces:
    - ProgressLogger (progress tracking)
    - ProcessRegistry (process tracking)
    - HeartbeatManager (health monitoring)
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern for database connection."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize database manager."""
        if hasattr(self, '_initialized'):
            return

        self.base_dir = Path(__file__).parent.parent.parent
        self.db_path = self.base_dir / "data" / "worker_state.db"

        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Thread-local storage for connections
        self._local = threading.local()

        # Initialize database
        self._initialize_database()

        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                check_same_thread=False
            )
            # Enable foreign keys
            self._local.connection.execute("PRAGMA foreign_keys = ON")
            # Enable WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode = WAL")
            # Return dictionaries instead of tuples
            self._local.connection.row_factory = sqlite3.Row

        return self._local.connection

    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e

    def _initialize_database(self):
        """Initialize database schema."""
        schema_path = self.base_dir / "backend" / "core" / "db_schema.sql"

        if not schema_path.exists():
            raise FileNotFoundError(f"Database schema not found: {schema_path}")

        # Read and execute schema
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        conn = self._get_connection()
        conn.executescript(schema_sql)
        conn.commit()

    # ========================================================================
    # WORKER MANAGEMENT
    # ========================================================================

    def initialize_workers(self, settings: Dict[str, Any]):
        """
        Initialize all workers from settings.

        Args:
            settings: Settings dictionary with annotator configurations
        """
        domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]

        with self.transaction() as conn:
            for annotator_id in [1, 2, 3, 4, 5]:
                for domain in domains:
                    try:
                        annotator_settings = settings["annotators"][str(annotator_id)]
                        domain_settings = annotator_settings[domain]

                        enabled = domain_settings.get("enabled", False)
                        target_count = domain_settings.get("target_count", 0)

                        # Insert or update worker
                        conn.execute('''
                            INSERT INTO workers (annotator_id, domain, enabled, target_count)
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT(annotator_id, domain)
                            DO UPDATE SET
                                enabled = excluded.enabled,
                                target_count = excluded.target_count
                        ''', (annotator_id, domain, enabled, target_count))

                    except (KeyError, TypeError):
                        # Worker not configured, insert with defaults
                        conn.execute('''
                            INSERT OR IGNORE INTO workers (annotator_id, domain, enabled, target_count)
                            VALUES (?, ?, ?, ?)
                        ''', (annotator_id, domain, False, 0))

    def get_worker_id(self, annotator_id: int, domain: str) -> Optional[int]:
        """Get database ID for worker."""
        conn = self._get_connection()
        result = conn.execute('''
            SELECT id FROM workers
            WHERE annotator_id = ? AND domain = ?
        ''', (annotator_id, domain)).fetchone()

        return result['id'] if result else None

    def get_or_create_worker(self, annotator_id: int, domain: str) -> int:
        """Get or create worker, return database ID."""
        worker_id = self.get_worker_id(annotator_id, domain)

        if worker_id is None:
            with self.transaction() as conn:
                cursor = conn.execute('''
                    INSERT INTO workers (annotator_id, domain)
                    VALUES (?, ?)
                ''', (annotator_id, domain))
                worker_id = cursor.lastrowid

        return worker_id

    def update_worker_status(self, annotator_id: int, domain: str, status: str,
                            pid: Optional[int] = None, log_event: bool = True):
        """Update worker status."""
        worker_id = self.get_or_create_worker(annotator_id, domain)

        with self.transaction() as conn:
            # Update status
            if status == 'running' and pid:
                conn.execute('''
                    UPDATE workers
                    SET status = ?, pid = ?, started_at = CURRENT_TIMESTAMP, last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, pid, worker_id))
            elif status in ['stopped', 'completed', 'crashed']:
                conn.execute('''
                    UPDATE workers
                    SET status = ?, pid = NULL, stopped_at = CURRENT_TIMESTAMP, last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, worker_id))
            else:
                conn.execute('''
                    UPDATE workers
                    SET status = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, worker_id))

            # Log event
            if log_event:
                conn.execute('''
                    INSERT INTO worker_events (worker_id, event_type)
                    VALUES (?, ?)
                ''', (worker_id, status))

    def update_worker_pid(self, annotator_id: int, domain: str, pid: int):
        """Update worker PID."""
        worker_id = self.get_or_create_worker(annotator_id, domain)

        with self.transaction() as conn:
            conn.execute('''
                UPDATE workers
                SET pid = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (pid, worker_id))

    def get_worker_status(self, annotator_id: int, domain: str) -> Dict[str, Any]:
        """Get comprehensive worker status."""
        conn = self._get_connection()

        result = conn.execute('''
            SELECT
                w.id,
                w.annotator_id,
                w.domain,
                w.status,
                w.enabled,
                w.pid,
                w.target_count,
                w.total_completed,
                w.total_malformed,
                w.samples_per_min,
                w.started_at,
                w.stopped_at,
                w.last_updated,
                h.heartbeat_time,
                h.iteration,
                CASE
                    WHEN h.heartbeat_time IS NULL THEN 0
                    WHEN (JULIANDAY('now') - JULIANDAY(h.heartbeat_time)) * 1440 > 2 THEN 0
                    ELSE 1
                END as heartbeat_alive
            FROM workers w
            LEFT JOIN heartbeats h ON w.id = h.worker_id
            WHERE w.annotator_id = ? AND w.domain = ?
        ''', (annotator_id, domain)).fetchone()

        if not result:
            return {
                "annotator_id": annotator_id,
                "domain": domain,
                "status": "not_configured",
                "error": "Worker not found in database"
            }

        # Convert to dict
        status = dict(result)

        # Check if stale (no heartbeat for 2+ minutes while running)
        if status['status'] == 'running' and not status['heartbeat_alive']:
            status['status'] = 'crashed'
            status['stale'] = True
        else:
            status['stale'] = False

        # Calculate progress
        status['progress'] = {
            "completed": status['total_completed'],
            "target": status['target_count'],
            "malformed": status['total_malformed'],
            "speed": status['samples_per_min'],
            "percentage": round((status['total_completed'] / status['target_count'] * 100)
                               if status['target_count'] > 0 else 0, 2)
        }

        # Check if running
        status['running'] = status['status'] == 'running' and status['heartbeat_alive']

        return status

    def get_all_worker_statuses(self) -> List[Dict[str, Any]]:
        """Get status of all workers."""
        domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
        statuses = []

        for annotator_id in [1, 2, 3, 4, 5]:
            for domain in domains:
                status = self.get_worker_status(annotator_id, domain)
                statuses.append(status)

        return statuses

    # ========================================================================
    # PROGRESS TRACKING
    # ========================================================================

    def add_completed_sample(self, annotator_id: int, domain: str,
                            sample_id: str, label: str, malformed: bool = False):
        """
        Add a completed sample to progress.

        Args:
            annotator_id: Annotator ID
            domain: Domain name
            sample_id: Sample ID
            label: Annotation label
            malformed: Whether response was malformed
        """
        worker_id = self.get_or_create_worker(annotator_id, domain)

        with self.transaction() as conn:
            # Insert into completed_samples
            conn.execute('''
                INSERT OR IGNORE INTO completed_samples
                (worker_id, sample_id, label, is_malformed)
                VALUES (?, ?, ?, ?)
            ''', (worker_id, sample_id, label, malformed))

            # Update worker statistics
            if malformed:
                conn.execute('''
                    UPDATE workers
                    SET total_malformed = total_malformed + 1,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (worker_id,))
            else:
                conn.execute('''
                    UPDATE workers
                    SET total_completed = total_completed + 1,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (worker_id,))

    def save_annotation(self, annotator_id: int, domain: str, annotation_data: Dict[str, Any]):
        """
        Save full annotation result.

        Args:
            annotator_id: Annotator ID
            domain: Domain name
            annotation_data: Annotation result dictionary
        """
        worker_id = self.get_or_create_worker(annotator_id, domain)

        with self.transaction() as conn:
            conn.execute('''
                INSERT INTO annotations
                (worker_id, sample_id, sample_text, label, response,
                 is_malformed, parsing_error, validity_error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                worker_id,
                annotation_data['id'],
                annotation_data['text'],
                annotation_data['label'],
                annotation_data.get('response'),
                annotation_data.get('malformed', False),
                annotation_data.get('parsing_error'),
                annotation_data.get('validity_error')
            ))

    def get_completed_count(self, annotator_id: int, domain: str) -> int:
        """Get number of completed samples."""
        conn = self._get_connection()

        result = conn.execute('''
            SELECT total_completed FROM workers
            WHERE annotator_id = ? AND domain = ?
        ''', (annotator_id, domain)).fetchone()

        return result['total_completed'] if result else 0

    def get_completed_ids(self, annotator_id: int, domain: str) -> List[str]:
        """Get list of completed sample IDs."""
        worker_id = self.get_worker_id(annotator_id, domain)
        if not worker_id:
            return []

        conn = self._get_connection()
        results = conn.execute('''
            SELECT sample_id FROM completed_samples
            WHERE worker_id = ? AND is_malformed = 0
            ORDER BY completed_at
        ''', (worker_id,)).fetchall()

        return [r['sample_id'] for r in results]

    def is_sample_completed(self, annotator_id: int, domain: str, sample_id: str) -> bool:
        """Check if sample has been completed."""
        worker_id = self.get_worker_id(annotator_id, domain)
        if not worker_id:
            return False

        conn = self._get_connection()
        result = conn.execute('''
            SELECT 1 FROM completed_samples
            WHERE worker_id = ? AND sample_id = ?
        ''', (worker_id, sample_id)).fetchone()

        return result is not None

    def update_speed(self, annotator_id: int, domain: str, samples_per_min: float):
        """Update processing speed."""
        worker_id = self.get_or_create_worker(annotator_id, domain)

        with self.transaction() as conn:
            conn.execute('''
                UPDATE workers
                SET samples_per_min = ?,
                    last_speed_check = CURRENT_TIMESTAMP,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (samples_per_min, worker_id))

    # ========================================================================
    # PROCESS REGISTRY
    # ========================================================================

    def register_worker_process(self, annotator_id: int, domain: str, pid: int):
        """Register worker process."""
        self.update_worker_status(annotator_id, domain, 'running', pid=pid, log_event=True)

    def unregister_worker_process(self, annotator_id: int, domain: str):
        """Unregister worker process."""
        worker_id = self.get_worker_id(annotator_id, domain)
        if not worker_id:
            return

        with self.transaction() as conn:
            conn.execute('''
                UPDATE workers
                SET pid = NULL, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (worker_id,))

            # Remove heartbeat
            conn.execute('DELETE FROM heartbeats WHERE worker_id = ?', (worker_id,))

    def get_worker_pid(self, annotator_id: int, domain: str) -> Optional[int]:
        """Get PID for worker."""
        conn = self._get_connection()

        result = conn.execute('''
            SELECT pid FROM workers
            WHERE annotator_id = ? AND domain = ?
        ''', (annotator_id, domain)).fetchone()

        return result['pid'] if result else None

    def is_worker_registered(self, annotator_id: int, domain: str) -> bool:
        """Check if worker is registered."""
        pid = self.get_worker_pid(annotator_id, domain)
        return pid is not None

    def _is_process_running(self, pid: int, annotator_id: int, domain: str) -> bool:
        """
        Check if process is actually running using /proc filesystem.

        Args:
            pid: Process ID
            annotator_id: Expected annotator ID
            domain: Expected domain

        Returns:
            True if process is running and is the correct worker
        """
        if pid is None or pid <= 0:
            return False

        try:
            # Check /proc/PID/cmdline (Linux-specific but most reliable)
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

        # Fallback to os.kill check (less reliable)
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def get_all_running_workers(self) -> List[Dict[str, Any]]:
        """
        Get all workers with running status and valid PIDs.
        Verifies processes are actually running using /proc filesystem.
        """
        conn = self._get_connection()

        results = conn.execute('''
            SELECT id, annotator_id, domain, pid, started_at
            FROM workers
            WHERE status = 'running' AND pid IS NOT NULL
        ''').fetchall()

        # Verify each process is actually running
        running_workers = []
        for r in results:
            worker_dict = dict(r)
            if self._is_process_running(worker_dict['pid'], worker_dict['annotator_id'], worker_dict['domain']):
                running_workers.append(worker_dict)
            else:
                # Process is dead, update status
                self.update_worker_status(worker_dict['annotator_id'], worker_dict['domain'], 'crashed', log_event=True)

        return running_workers

    # ========================================================================
    # HEARTBEAT MANAGEMENT
    # ========================================================================

    def send_heartbeat(self, annotator_id: int, domain: str,
                      iteration: int = 0, heartbeat_status: str = "running"):
        """Send worker heartbeat."""
        worker_id = self.get_or_create_worker(annotator_id, domain)
        pid = os.getpid()

        with self.transaction() as conn:
            conn.execute('''
                INSERT INTO heartbeats (worker_id, pid, iteration, heartbeat_status, heartbeat_time)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(worker_id)
                DO UPDATE SET
                    pid = excluded.pid,
                    iteration = excluded.iteration,
                    heartbeat_status = excluded.heartbeat_status,
                    heartbeat_time = CURRENT_TIMESTAMP
            ''', (worker_id, pid, iteration, heartbeat_status))

    def is_heartbeat_alive(self, annotator_id: int, domain: str, timeout_minutes: int = 2) -> bool:
        """Check if worker heartbeat is recent."""
        worker_id = self.get_worker_id(annotator_id, domain)
        if not worker_id:
            return False

        conn = self._get_connection()
        result = conn.execute('''
            SELECT
                (JULIANDAY('now') - JULIANDAY(heartbeat_time)) * 1440 as minutes_ago
            FROM heartbeats
            WHERE worker_id = ?
        ''', (worker_id,)).fetchone()

        if not result:
            return False

        return result['minutes_ago'] < timeout_minutes

    def cleanup_heartbeat(self, annotator_id: int, domain: str):
        """Remove heartbeat for worker."""
        worker_id = self.get_worker_id(annotator_id, domain)
        if not worker_id:
            return

        with self.transaction() as conn:
            conn.execute('DELETE FROM heartbeats WHERE worker_id = ?', (worker_id,))

    def get_stuck_workers(self) -> List[Dict[str, Any]]:
        """Find workers with stale heartbeats."""
        conn = self._get_connection()

        results = conn.execute('''
            SELECT
                w.id,
                w.annotator_id,
                w.domain,
                w.pid,
                h.heartbeat_time,
                (JULIANDAY('now') - JULIANDAY(h.heartbeat_time)) * 1440 as minutes_ago
            FROM workers w
            JOIN heartbeats h ON w.id = h.worker_id
            WHERE w.status = 'running'
              AND (JULIANDAY('now') - JULIANDAY(h.heartbeat_time)) * 1440 > 2
        ''').fetchall()

        return [dict(r) for r in results]

    # ========================================================================
    # MONITORING & ANALYTICS
    # ========================================================================

    def get_system_overview(self) -> Dict[str, Any]:
        """Get system-wide statistics."""
        conn = self._get_connection()

        result = conn.execute('''
            SELECT * FROM v_system_overview
        ''').fetchone()

        overview = dict(result) if result else {}

        # Calculate estimated time
        total_completed = overview.get('total_completed_samples', 0)
        total_target = overview.get('total_target_samples', 0)
        avg_speed = overview.get('avg_speed', 0)

        remaining_samples = total_target - total_completed
        if avg_speed > 0:
            remaining_minutes = remaining_samples / avg_speed
            hours = int(remaining_minutes // 60)
            minutes = int(remaining_minutes % 60)
            overview['estimated_time_remaining'] = f"{hours}h {minutes}m"
        else:
            overview['estimated_time_remaining'] = "Unknown"

        return overview

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent worker events."""
        conn = self._get_connection()

        results = conn.execute('''
            SELECT * FROM v_recent_events
            LIMIT ?
        ''', (limit,)).fetchall()

        return [dict(r) for r in results]

    # ========================================================================
    # FACTORY RESET
    # ========================================================================

    def factory_reset(self):
        """
        Complete factory reset - delete all progress and state data.
        Preserves worker configuration (enabled, target_count).
        """
        with self.transaction() as conn:
            # Delete all progress data
            conn.execute('DELETE FROM annotations')
            conn.execute('DELETE FROM completed_samples')
            conn.execute('DELETE FROM heartbeats')
            conn.execute('DELETE FROM worker_events')
            conn.execute('DELETE FROM rate_limiter_state')

            # Reset worker state but keep configuration
            conn.execute('''
                UPDATE workers
                SET status = 'not_started',
                    pid = NULL,
                    started_at = NULL,
                    stopped_at = NULL,
                    total_completed = 0,
                    total_malformed = 0,
                    samples_per_min = 0.0,
                    last_speed_check = NULL,
                    last_updated = CURRENT_TIMESTAMP
            ''')

            # Update system state
            conn.execute('''
                INSERT OR REPLACE INTO system_state (key, value, updated_at)
                VALUES ('last_factory_reset', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''')

            # Vacuum to reclaim space
            conn.execute('VACUUM')

    def reset_worker(self, annotator_id: int, domain: str):
        """Reset specific worker progress."""
        worker_id = self.get_worker_id(annotator_id, domain)
        if not worker_id:
            return

        with self.transaction() as conn:
            # Delete progress data
            conn.execute('DELETE FROM annotations WHERE worker_id = ?', (worker_id,))
            conn.execute('DELETE FROM completed_samples WHERE worker_id = ?', (worker_id,))
            conn.execute('DELETE FROM heartbeats WHERE worker_id = ?', (worker_id,))

            # Reset worker state
            conn.execute('''
                UPDATE workers
                SET status = 'not_started',
                    pid = NULL,
                    started_at = NULL,
                    stopped_at = NULL,
                    total_completed = 0,
                    total_malformed = 0,
                    samples_per_min = 0.0,
                    last_speed_check = NULL,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (worker_id,))

            # Log event
            conn.execute('''
                INSERT INTO worker_events (worker_id, event_type)
                VALUES (?, 'reset')
            ''', (worker_id,))

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def close(self):
        """Close database connection."""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            del self._local.connection

    def optimize(self):
        """Optimize database (VACUUM and ANALYZE)."""
        conn = self._get_connection()
        conn.execute('VACUUM')
        conn.execute('ANALYZE')


# Global instance
_db = None


def get_db() -> DatabaseManager:
    """Get global database instance."""
    global _db
    if _db is None:
        _db = DatabaseManager()
    return _db
