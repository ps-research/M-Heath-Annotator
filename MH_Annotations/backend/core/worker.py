"""
Worker process for annotating samples.

Each worker handles one annotator-domain pair.

UPGRADED: Now includes heartbeat monitoring, rate limiting, and structured logging.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.annotator import GeminiAnnotator
from backend.core.parser import ResponseParser
from backend.core.progress_logger import ProgressLogger
from backend.core.dataset_loader import DatasetLoader
from backend.core.heartbeat_manager import WorkerHeartbeat
from backend.core.rate_limiter import RateLimiter
from backend.core.logger_config import get_worker_logger
from backend.utils.file_operations import atomic_read_json, atomic_write_json, ensure_directory


class AnnotationWorker:
    """
    Main worker class for annotation process.

    Handles:
    - Loading configuration and dataset
    - Processing samples with checkpointing
    - Control signal handling (pause/resume/stop)
    - Progress tracking
    - Error handling
    """

    def __init__(self, annotator_id: int, domain: str):
        """
        Initialize worker.

        Args:
            annotator_id: Annotator ID (1-5)
            domain: Domain name

        Raises:
            ValueError: If configuration is invalid
            FileNotFoundError: If required files are missing
        """
        self.annotator_id = annotator_id
        self.domain = domain

        # Setup logger
        self.logger = get_worker_logger(annotator_id, domain)

        # Validate inputs
        if annotator_id not in [1, 2, 3, 4, 5]:
            raise ValueError(f"Invalid annotator_id: {annotator_id}")

        valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
        if domain not in valid_domains:
            raise ValueError(f"Invalid domain: {domain}")

        # Set base directory
        self.base_dir = Path(__file__).parent.parent.parent

        # Load settings
        settings_path = self.base_dir / "config" / "settings.json"
        self.settings = atomic_read_json(str(settings_path))
        if not self.settings:
            raise FileNotFoundError(f"Settings file not found: {settings_path}")

        # Load API key
        api_keys_path = self.base_dir / "config" / "api_keys.json"
        api_keys = atomic_read_json(str(api_keys_path))
        if not api_keys:
            raise FileNotFoundError(f"API keys file not found: {api_keys_path}")

        self.api_key = api_keys.get(f"annotator_{annotator_id}", "")
        if not self.api_key or self.api_key.strip() == "":
            raise ValueError(f"API key not found for annotator {annotator_id}")

        # Get model name from settings
        model_name = self.settings["global"]["model_name"]

        # Initialize components
        self.gemini = GeminiAnnotator(self.api_key, model_name)
        self.parser = ResponseParser()
        self.progress_logger = ProgressLogger(annotator_id, domain)

        # Initialize NEW systems
        self.heartbeat = WorkerHeartbeat(annotator_id, domain, interval=30)
        self.rate_limiter = RateLimiter(
            requests_per_minute=15,
            requests_per_day=1500,
            burst_size=5
        )
        self.api_key_id = f"annotator_{annotator_id}"

        # Initialize dataset loader
        dataset_path = self.base_dir / "data" / "source" / "m_help_dataset.xlsx"
        self.dataset_loader = DatasetLoader(str(dataset_path))

        # Load dataset immediately to fail fast if file is missing
        try:
            self.dataset_loader.load()
        except FileNotFoundError as e:
            self.logger.error(f"Dataset file not found: {dataset_path}")
            self.logger.error("Please place your Excel file at this location.")
            raise

        # Set control file path
        self.control_file_path = self.base_dir / "control" / f"annotator_{annotator_id}_{domain}.json"

        # Set annotations file path
        annotations_dir = self.base_dir / "data" / "annotations" / f"annotator_{annotator_id}" / domain
        ensure_directory(str(annotations_dir))
        self.annotations_file_path = annotations_dir / "annotations.jsonl"

        # Control loop tracking
        self.iteration_count = 0
        self.last_control_check_time = time.time()
        self.should_stop_flag = False

        self.logger.info(f"Worker initialized for Annotator {annotator_id}, Domain {domain}")

    def load_prompt(self) -> str:
        """
        Load prompt template for this domain.

        Checks for override first, then falls back to base prompt.

        Returns:
            Prompt template string with {text} placeholder

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        # Check for override first
        override_path = self.base_dir / "config" / "prompts" / "overrides" / f"annotator_{self.annotator_id}" / f"{self.domain}.txt"

        if override_path.exists():
            print(f"📝 Loading override prompt from {override_path}")
            with open(override_path, 'r', encoding='utf-8') as f:
                return f.read()

        # Fall back to base prompt
        base_path = self.base_dir / "config" / "prompts" / "base" / f"{self.domain}.txt"

        if not base_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {base_path}\n"
                f"Please ensure prompt templates are in config/prompts/base/"
            )

        with open(base_path, 'r', encoding='utf-8') as f:
            return f.read()

    def get_next_sample(self) -> Optional[Dict[str, str]]:
        """
        Get next sample to annotate.

        Returns:
            Sample dict with 'id' and 'text', or None if done
        """
        # Load current progress
        progress = self.progress_logger.load()

        # Check if target reached
        completed_count = len(progress["completed_ids"])
        target_count = progress["target_count"]

        if completed_count >= target_count:
            return None

        # Get sample by index (sequential processing)
        sample = self.dataset_loader.get_sample_by_index(completed_count)

        return sample

    def should_check_control(self) -> bool:
        """
        Determine if control signal should be checked.

        Checks every 5 iterations OR every 10 seconds, whichever comes first.

        Returns:
            True if control should be checked
        """
        # Check iteration count
        check_iterations = self.settings["global"]["control_check_iterations"]
        if self.iteration_count % check_iterations == 0:
            return True

        # Check time elapsed
        check_seconds = self.settings["global"]["control_check_seconds"]
        elapsed = time.time() - self.last_control_check_time
        if elapsed >= check_seconds:
            return True

        return False

    def check_control_signal(self) -> Optional[str]:
        """
        Check for control signal file.

        Returns:
            Command string ("pause", "resume", "stop") or None
        """
        if not self.control_file_path.exists():
            return None

        try:
            control_data = atomic_read_json(str(self.control_file_path))
            if not control_data:
                return None

            command = control_data.get("command")

            # Validate command
            valid_commands = ["pause", "resume", "stop"]
            if command not in valid_commands:
                print(f"⚠️  Invalid control command: {command}")
                return None

            return command

        except Exception as e:
            print(f"⚠️  Error reading control file: {str(e)}")
            return None

    def handle_pause(self) -> None:
        """
        Handle pause command - enter wait loop until resumed or stopped.
        """
        self.logger.info("Worker paused")
        self.progress_logger.update_status("paused")
        self.heartbeat.send_now("paused")

        # Enter pause loop
        while True:
            time.sleep(5)  # Check every 5 seconds

            # Send heartbeat while paused
            self.heartbeat.maybe_send("paused")

            command = self.check_control_signal()

            if command == "resume":
                self.logger.info("Worker resumed")
                self.progress_logger.update_status("running")
                self.heartbeat.send_now("running")
                self.last_control_check_time = time.time()
                break

            elif command == "stop":
                self.logger.info("Stop signal received during pause")
                self.should_stop_flag = True
                break

    def handle_stop(self) -> None:
        """
        Handle stop command - set flag to exit gracefully.
        """
        self.logger.info("Worker stopping gracefully")
        self.progress_logger.update_status("stopped")
        self.heartbeat.send_now("stopped")
        self.should_stop_flag = True

    def annotate_sample(self, sample: Dict[str, str], prompt_template: str) -> Dict[str, Any]:
        """
        Annotate a single sample.

        Args:
            sample: Sample dict with 'id' and 'text'
            prompt_template: Prompt template with {text} placeholder

        Returns:
            Result dictionary with annotation data

        Raises:
            Exception: If rate limit hit or invalid API key
        """
        # Acquire rate limit permission
        if not self.rate_limiter.acquire_sync(self.api_key_id, timeout=300):
            self.logger.error(f"Rate limit timeout for sample {sample['id']}")
            raise Exception("RATE_LIMIT_TIMEOUT")

        # Format prompt
        prompt = prompt_template.format(text=sample['text'])

        # Call Gemini API
        response_text, error = self.gemini.generate(prompt)

        # Handle API errors
        if error:
            if error == "RATE_LIMIT":
                print(f"\n❌ Rate limit hit for sample {sample['id']}")
                self.progress_logger.update_status("paused")
                raise Exception("RATE_LIMIT_HIT")

            elif error == "INVALID_KEY":
                print(f"\n❌ Invalid API key")
                raise Exception("INVALID_API_KEY")

            else:
                # Other API error - log and return error result
                print(f"\n⚠️  API error for sample {sample['id']}: {error}")
                return {
                    "id": sample['id'],
                    "text": sample['text'],
                    "response": f"API_ERROR: {error}",
                    "label": "MALFORMED",
                    "malformed": True,
                    "parsing_error": None,
                    "validity_error": error,
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                }

        # Parse response
        label, parsing_error, validity_error = self.parser.parse_response(response_text, self.domain)

        # Determine if malformed
        malformed = (parsing_error is not None) or (validity_error is not None)

        # Construct result
        result = {
            "id": sample['id'],
            "text": sample['text'],
            "response": response_text,
            "label": label if label else "MALFORMED",
            "malformed": malformed,
            "parsing_error": parsing_error,
            "validity_error": validity_error,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }

        return result

    def save_annotation(self, result: Dict[str, Any]) -> None:
        """
        Save annotation result to JSONL file.

        Args:
            result: Annotation result dictionary
        """
        try:
            # Append to JSONL file
            with open(self.annotations_file_path, 'a') as f:
                json.dump(result, f)
                f.write('\n')
                f.flush()

        except Exception as e:
            print(f"❌ Error saving annotation: {str(e)}")
            raise

    def run(self) -> None:
        """
        Main worker loop.

        Processes samples until target reached or stopped.
        """
        self.logger.info("="*70)
        self.logger.info(f"Worker starting for Annotator {self.annotator_id}, Domain {self.domain}")
        self.logger.info("="*70)

        # Initialize
        progress = self.progress_logger.load()
        self.progress_logger.update_status("running")
        self.progress_logger.update_pid(os.getpid())
        self.progress_logger.set_start_time()

        # Start heartbeat
        self.heartbeat.start()

        # Load prompt template
        try:
            prompt_template = self.load_prompt()
        except FileNotFoundError as e:
            self.logger.error(str(e))
            self.progress_logger.update_status("stopped")
            return

        # Get settings
        request_delay = self.settings["global"]["request_delay_seconds"]

        # Track start time for speed calculation
        start_time = time.time()

        self.logger.info(f"Target: {progress['target_count']} samples")
        self.logger.info(f"Already completed: {len(progress['completed_ids'])} samples")
        self.logger.info("Starting annotation loop...")

        # Main loop
        while not self.should_stop_flag:
            self.iteration_count += 1
            self.heartbeat.increment_iteration()

            # Send heartbeat periodically
            self.heartbeat.maybe_send("running")

            # Check control signals
            if self.should_check_control():
                self.last_control_check_time = time.time()
                command = self.check_control_signal()

                if command == "pause":
                    self.handle_pause()
                    continue

                elif command == "stop":
                    self.handle_stop()
                    break

            # Get next sample
            sample = self.get_next_sample()

            if sample is None:
                # No more samples or target reached
                self.logger.info("Target reached!")
                self.progress_logger.update_status("completed")
                self.heartbeat.send_now("completed")
                break

            try:
                # Annotate sample
                result = self.annotate_sample(sample, prompt_template)

                # Save annotation
                self.save_annotation(result)

                # Update progress
                self.progress_logger.add_completed(
                    sample['id'],
                    result['label'],
                    result['malformed']
                )

                # Log progress
                if result['malformed']:
                    self.logger.warning(f"Sample {sample['id']}: MALFORMED")
                else:
                    self.logger.info(f"Sample {sample['id']}: {result['label']}")

                # Update speed every 10 samples
                if self.iteration_count % 10 == 0:
                    elapsed = time.time() - start_time
                    progress = self.progress_logger.load()
                    samples_done = len(progress['completed_ids'])
                    self.progress_logger.update_speed(samples_done, elapsed)

                    speed = progress['stats']['samples_per_min']
                    self.logger.info(f"Speed: {speed:.2f} samples/min")

                # Rate limiting delay
                time.sleep(request_delay)

            except Exception as e:
                error_str = str(e)

                if "RATE_LIMIT" in error_str:
                    self.logger.warning("Paused due to rate limit. Exiting...")
                    self.heartbeat.send_now("paused")
                    break

                elif "INVALID_API_KEY" in error_str:
                    self.logger.error("Invalid API key. Exiting...")
                    self.progress_logger.update_status("stopped")
                    self.heartbeat.send_now("stopped")
                    break

                else:
                    # Log unexpected error and continue
                    self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
                    self.logger.info("Continuing to next sample...")
                    continue

        # Cleanup
        self.logger.info("="*70)
        self.logger.info(f"Worker finished for Annotator {self.annotator_id}, Domain {self.domain}")
        self.logger.info("="*70)

        final_progress = self.progress_logger.load()
        self.logger.info(f"Completed: {len(final_progress['completed_ids'])} samples")
        self.logger.info(f"Malformed: {len(final_progress['malformed_ids'])} samples")
        self.logger.info(f"Final status: {final_progress['status']}")

        # Cleanup heartbeat
        self.heartbeat.cleanup()


def main():
    """Entry point for worker subprocess."""
    parser = argparse.ArgumentParser(description="Annotation Worker")
    parser.add_argument("--annotator", type=int, required=True, help="Annotator ID (1-5)")
    parser.add_argument("--domain", type=str, required=True, help="Domain name")

    args = parser.parse_args()

    # Validate inputs
    if args.annotator not in [1, 2, 3, 4, 5]:
        print(f"❌ Error: Invalid annotator ID: {args.annotator}")
        sys.exit(1)

    valid_domains = ["urgency", "therapeutic", "intensity", "adjunct", "modality", "redressal"]
    if args.domain not in valid_domains:
        print(f"❌ Error: Invalid domain: {args.domain}")
        print(f"   Valid domains: {', '.join(valid_domains)}")
        sys.exit(1)

    # Create and run worker
    try:
        worker = AnnotationWorker(args.annotator, args.domain)
        worker.run()
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
