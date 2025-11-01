"""
Global rate limiter for coordinating API calls across multiple workers.

Implements token bucket algorithm to prevent API quota exhaustion.
Works with file-based storage (no Redis required).
"""

import time
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timezone
import sys
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.utils.file_operations import atomic_read_json, atomic_write_json, ensure_directory


class RateLimiter:
    """
    File-based rate limiter using token bucket algorithm.

    Each API key has its own rate limit tracking.
    Coordinates across all workers to prevent quota exhaustion.
    """

    def __init__(
        self,
        requests_per_minute: int = 15,
        requests_per_day: int = 1500,
        burst_size: int = 5
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute per API key
            requests_per_day: Max requests per day per API key
            burst_size: Max burst of requests allowed
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        self.burst_size = burst_size

        self.base_dir = Path(__file__).parent.parent.parent
        self.limiter_dir = self.base_dir / "data" / "rate_limiter"
        ensure_directory(str(self.limiter_dir))

        # Time between requests (seconds)
        self.min_interval = 60.0 / requests_per_minute

    def _get_limiter_path(self, api_key_id: str) -> Path:
        """Get path to rate limiter state file."""
        # Use sanitized key name (e.g., "annotator_1")
        return self.limiter_dir / f"{api_key_id}.json"

    def _load_state(self, api_key_id: str) -> Dict:
        """Load rate limiter state."""
        limiter_path = self._get_limiter_path(api_key_id)
        state = atomic_read_json(str(limiter_path))

        if state is None:
            # Initialize new state
            state = {
                "tokens": self.burst_size,
                "last_refill": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "requests_today": 0,
                "day_start": datetime.now(timezone.utc).date().isoformat(),
                "total_requests": 0,
                "last_request": None
            }
            self._save_state(api_key_id, state)

        return state

    def _save_state(self, api_key_id: str, state: Dict) -> None:
        """Save rate limiter state."""
        limiter_path = self._get_limiter_path(api_key_id)
        atomic_write_json(state, str(limiter_path))

    def _refill_tokens(self, state: Dict) -> Dict:
        """Refill tokens based on elapsed time."""
        now = datetime.now(timezone.utc)
        last_refill = datetime.fromisoformat(state["last_refill"].replace('Z', '+00:00'))

        # Calculate elapsed time
        elapsed = (now - last_refill).total_seconds()

        # Refill rate: tokens per second
        refill_rate = self.requests_per_minute / 60.0

        # Add tokens
        tokens_to_add = elapsed * refill_rate
        state["tokens"] = min(state["tokens"] + tokens_to_add, self.burst_size)
        state["last_refill"] = now.isoformat().replace('+00:00', 'Z')

        return state

    def _check_daily_limit(self, state: Dict) -> bool:
        """Check if daily limit is exceeded."""
        today = datetime.now(timezone.utc).date().isoformat()

        # Reset counter if new day
        if state["day_start"] != today:
            state["day_start"] = today
            state["requests_today"] = 0

        # Check if limit exceeded
        return state["requests_today"] < self.requests_per_day

    def can_make_request(self, api_key_id: str) -> tuple[bool, Optional[float]]:
        """
        Check if request can be made.

        Args:
            api_key_id: API key identifier (e.g., "annotator_1")

        Returns:
            Tuple of (can_proceed, wait_time_seconds)
        """
        state = self._load_state(api_key_id)

        # Refill tokens
        state = self._refill_tokens(state)

        # Check daily limit
        if not self._check_daily_limit(state):
            return False, None  # Daily limit exceeded, no point waiting

        # Check if we have tokens
        if state["tokens"] >= 1.0:
            return True, 0.0
        else:
            # Calculate wait time
            tokens_needed = 1.0 - state["tokens"]
            wait_time = tokens_needed / (self.requests_per_minute / 60.0)
            return False, wait_time

    async def acquire(self, api_key_id: str, timeout: float = 300.0) -> bool:
        """
        Acquire permission to make API request (async).

        Waits until request can be made or timeout is reached.

        Args:
            api_key_id: API key identifier (e.g., "annotator_1")
            timeout: Max wait time in seconds

        Returns:
            True if acquired, False if timeout
        """
        start_time = time.time()

        while True:
            can_proceed, wait_time = self.can_make_request(api_key_id)

            if can_proceed:
                # Consume token
                self.consume_token(api_key_id)
                return True

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                return False

            # Wait before retrying
            if wait_time is None:
                # Daily limit exceeded
                return False

            await asyncio.sleep(min(wait_time + 0.1, 5.0))  # Wait with max 5s intervals

    def acquire_sync(self, api_key_id: str, timeout: float = 300.0) -> bool:
        """
        Acquire permission to make API request (synchronous).

        Waits until request can be made or timeout is reached.

        Args:
            api_key_id: API key identifier (e.g., "annotator_1")
            timeout: Max wait time in seconds

        Returns:
            True if acquired, False if timeout
        """
        start_time = time.time()

        while True:
            can_proceed, wait_time = self.can_make_request(api_key_id)

            if can_proceed:
                # Consume token
                self.consume_token(api_key_id)
                return True

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                return False

            # Wait before retrying
            if wait_time is None:
                # Daily limit exceeded
                return False

            time.sleep(min(wait_time + 0.1, 5.0))  # Wait with max 5s intervals

    def consume_token(self, api_key_id: str) -> None:
        """
        Consume a token (record an API request).

        Args:
            api_key_id: API key identifier
        """
        state = self._load_state(api_key_id)

        # Refill first
        state = self._refill_tokens(state)

        # Consume token
        state["tokens"] = max(0, state["tokens"] - 1.0)
        state["requests_today"] += 1
        state["total_requests"] += 1
        state["last_request"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        self._save_state(api_key_id, state)

    def get_status(self, api_key_id: str) -> Dict:
        """
        Get rate limiter status for an API key.

        Args:
            api_key_id: API key identifier

        Returns:
            Status dictionary
        """
        state = self._load_state(api_key_id)
        state = self._refill_tokens(state)

        can_proceed, wait_time = self.can_make_request(api_key_id)

        return {
            "api_key_id": api_key_id,
            "tokens_available": state["tokens"],
            "max_tokens": self.burst_size,
            "requests_today": state["requests_today"],
            "daily_limit": self.requests_per_day,
            "percentage_used": (state["requests_today"] / self.requests_per_day * 100),
            "can_make_request": can_proceed,
            "wait_time_seconds": wait_time,
            "last_request": state.get("last_request"),
            "requests_per_minute": self.requests_per_minute
        }

    def get_all_statuses(self) -> Dict[str, Dict]:
        """
        Get status for all API keys.

        Returns:
            Dictionary mapping api_key_id to status
        """
        statuses = {}

        for limiter_file in self.limiter_dir.glob("*.json"):
            api_key_id = limiter_file.stem
            statuses[api_key_id] = self.get_status(api_key_id)

        return statuses

    def reset_daily_counters(self) -> None:
        """Reset daily request counters for all keys."""
        for limiter_file in self.limiter_dir.glob("*.json"):
            api_key_id = limiter_file.stem
            state = self._load_state(api_key_id)
            state["requests_today"] = 0
            state["day_start"] = datetime.now(timezone.utc).date().isoformat()
            self._save_state(api_key_id, state)

    def reset_all(self) -> None:
        """Reset all rate limiter state."""
        for limiter_file in self.limiter_dir.glob("*.json"):
            try:
                limiter_file.unlink()
            except Exception:
                pass
