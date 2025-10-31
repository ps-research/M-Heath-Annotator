"""
Progress tracking for individual annotator-domain pairs.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.utils.file_operations import atomic_read_json, atomic_write_json, ensure_directory


class ProgressLogger:
    """
    Manages progress tracking for a single annotator-domain pair.

    Provides atomic checkpoint operations for crash recovery.
    """

    VALID_DOMAINS = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    VALID_STATUSES = ["not_started", "running", "paused", "stopped", "completed", "crashed"]

    def __init__(self, annotator_id: int, domain: str):
        """
        Initialize progress logger.

        Args:
            annotator_id: Annotator ID (1-5)
            domain: Domain name

        Raises:
            ValueError: If annotator_id or domain is invalid
        """
        # Validate inputs
        if annotator_id not in [1, 2, 3, 4, 5]:
            raise ValueError(f"Invalid annotator_id: {annotator_id}. Must be 1-5.")

        if domain not in self.VALID_DOMAINS:
            raise ValueError(
                f"Invalid domain: {domain}. Must be one of {self.VALID_DOMAINS}"
            )

        self.annotator_id = annotator_id
        self.domain = domain

        # Construct progress file path
        base_dir = Path(__file__).parent.parent.parent
        progress_dir = base_dir / "data" / "annotations" / f"annotator_{annotator_id}" / domain
        self.progress_path = progress_dir / "progress.json"

        # Ensure directory exists
        ensure_directory(str(progress_dir))

        # Cache for progress data
        self.progress_data: Optional[Dict[str, Any]] = None

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings for this annotator-domain pair."""
        base_dir = Path(__file__).parent.parent.parent
        settings_path = base_dir / "config" / "settings.json"

        settings = atomic_read_json(str(settings_path))
        if not settings:
            # Default settings if file doesn't exist
            return {"enabled": False, "target_count": 0}

        try:
            annotator_settings = settings["annotators"][str(self.annotator_id)]
            domain_settings = annotator_settings[self.domain]
            return domain_settings
        except (KeyError, TypeError):
            return {"enabled": False, "target_count": 0}

    def load(self) -> Dict[str, Any]:
        """
        Load progress from file or create new.

        Returns:
            Progress data dictionary
        """
        # Try to load existing progress
        progress_data = atomic_read_json(str(self.progress_path))

        if progress_data is None:
            # Create new progress file
            domain_settings = self._load_settings()

            progress_data = {
                "annotator_id": self.annotator_id,
                "domain": self.domain,
                "enabled": domain_settings.get("enabled", False),
                "target_count": domain_settings.get("target_count", 0),
                "status": "not_started",
                "completed_ids": [],
                "malformed_ids": [],
                "last_processed_id": None,
                "last_updated": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "pid": None,
                "stats": {
                    "total_completed": 0,
                    "malformed_count": 0,
                    "start_time": None,
                    "last_speed_check": None,
                    "samples_per_min": 0.0
                }
            }

            # Save initial progress
            self.save(progress_data)

        # Cache the data
        self.progress_data = progress_data
        return progress_data

    def save(self, progress_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Save progress to file atomically.

        Args:
            progress_data: Progress data to save (uses cached if None)
        """
        if progress_data is None:
            if self.progress_data is None:
                raise ValueError("No progress data to save")
            progress_data = self.progress_data

        # Update timestamps and counts
        progress_data["last_updated"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        progress_data["stats"]["total_completed"] = len(progress_data.get("completed_ids", []))
        progress_data["stats"]["malformed_count"] = len(progress_data.get("malformed_ids", []))

        # Atomic write
        atomic_write_json(progress_data, str(self.progress_path))

        # Update cache
        self.progress_data = progress_data

    def add_completed(self, sample_id: str, label: str, malformed: bool = False) -> None:
        """
        Add a completed sample to progress.

        Args:
            sample_id: Sample ID
            label: Annotation label
            malformed: Whether response was malformed
        """
        # Load current progress
        progress = self.load()

        if malformed:
            # Add to malformed list
            if sample_id not in progress["malformed_ids"]:
                progress["malformed_ids"].append(sample_id)
        else:
            # Add to completed list
            if sample_id not in progress["completed_ids"]:
                progress["completed_ids"].append(sample_id)

        # Update last processed ID
        progress["last_processed_id"] = sample_id

        # Save updated progress
        self.save(progress)

    def get_completed_count(self) -> int:
        """
        Get number of completed samples.

        Returns:
            Count of completed samples
        """
        progress = self.load()
        return len(progress["completed_ids"])

    def get_pending_count(self, total_available: int) -> int:
        """
        Get number of pending samples.

        Args:
            total_available: Total samples in dataset

        Returns:
            Number of samples remaining to annotate
        """
        progress = self.load()
        target = progress["target_count"]
        completed = len(progress["completed_ids"])

        # Pending is min(target, total_available) - completed
        pending = max(0, min(target, total_available) - completed)
        return pending

    def is_complete(self) -> bool:
        """
        Check if annotation is complete.

        Returns:
            True if target reached
        """
        progress = self.load()
        completed = len(progress["completed_ids"])
        target = progress["target_count"]
        return completed >= target

    def update_status(self, new_status: str) -> None:
        """
        Update worker status.

        Args:
            new_status: New status value

        Raises:
            ValueError: If status is invalid
        """
        if new_status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid status: {new_status}. Must be one of {self.VALID_STATUSES}"
            )

        progress = self.load()
        progress["status"] = new_status
        self.save(progress)

    def update_speed(self, samples_processed: int, time_elapsed_seconds: float) -> None:
        """
        Update processing speed statistics.

        Args:
            samples_processed: Number of samples processed
            time_elapsed_seconds: Time elapsed in seconds
        """
        if time_elapsed_seconds <= 0:
            return

        # Calculate samples per minute
        samples_per_min = (samples_processed / time_elapsed_seconds) * 60

        progress = self.load()
        progress["stats"]["samples_per_min"] = round(samples_per_min, 2)
        progress["stats"]["last_speed_check"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        self.save(progress)

    def is_stale(self, minutes: int = 5) -> bool:
        """
        Check if progress is stale (not updated recently).

        Args:
            minutes: Threshold in minutes

        Returns:
            True if progress hasn't been updated within threshold
        """
        progress = self.load()
        last_updated_str = progress.get("last_updated")

        if not last_updated_str:
            return True

        try:
            # Parse timestamp
            last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)

            # Calculate time difference
            time_diff = now - last_updated
            return time_diff.total_seconds() > (minutes * 60)

        except Exception as e:
            print(f"Error checking staleness: {str(e)}")
            return True

    def update_pid(self, pid: int) -> None:
        """
        Update process ID.

        Args:
            pid: Process ID
        """
        progress = self.load()
        progress["pid"] = pid
        self.save(progress)

    def set_start_time(self) -> None:
        """Set start time if not already set."""
        progress = self.load()
        if progress["stats"]["start_time"] is None:
            progress["stats"]["start_time"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            self.save(progress)
