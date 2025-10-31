"""
Example usage of the Worker Manager.

This script demonstrates how to:
1. Start workers
2. Monitor progress
3. Control workers (pause/resume/stop)
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.worker_manager import WorkerManager


def example_start_single_worker():
    """Example: Start a single worker."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Start Single Worker")
    print("="*60)

    manager = WorkerManager()

    # Start worker for annotator 1, urgency domain
    result = manager.start_worker(1, "urgency")

    print(f"\nResult: {result['status']}")
    if result['status'] == 'started':
        print(f"PID: {result['pid']}")


def example_start_all_enabled():
    """Example: Start all enabled workers."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Start All Enabled Workers")
    print("="*60)

    manager = WorkerManager()

    # Start all enabled workers
    result = manager.start_all_enabled()

    print(f"\nStarted: {result['started']} workers")
    print(f"Disabled: {result['disabled']} workers")
    print(f"Failed: {result['failed']} workers")


def example_monitor_progress():
    """Example: Monitor worker progress."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Monitor Progress")
    print("="*60)

    manager = WorkerManager()

    # Get status for specific worker
    status = manager.get_worker_status(1, "urgency")

    print(f"\nAnnotator: {status['annotator_id']}")
    print(f"Domain: {status['domain']}")
    print(f"Status: {status['status']}")
    print(f"Running: {status['running']}")
    print(f"Completed: {status['progress']['completed']}/{status['progress']['target']}")
    print(f"Malformed: {status['progress']['malformed']}")
    print(f"Speed: {status['progress']['speed']:.2f} samples/min")
    print(f"Last updated: {status['last_updated']}")


def example_monitor_all():
    """Example: Monitor all workers."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Monitor All Workers")
    print("="*60)

    manager = WorkerManager()

    # Get all statuses
    all_statuses = manager.get_all_statuses()

    # Filter to only show enabled workers
    enabled = [s for s in all_statuses if s['progress']['target'] > 0]

    if not enabled:
        print("\nNo enabled workers found")
        return

    print(f"\nFound {len(enabled)} enabled workers:\n")

    for status in enabled:
        completed = status['progress']['completed']
        target = status['progress']['target']
        percent = (completed / target * 100) if target > 0 else 0

        print(f"Annotator {status['annotator_id']}, {status['domain']:12s} | "
              f"Status: {status['status']:10s} | "
              f"Progress: {completed:3d}/{target:3d} ({percent:5.1f}%) | "
              f"Speed: {status['progress']['speed']:5.1f} samples/min")


def example_control_workers():
    """Example: Control workers (pause/resume/stop)."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Control Workers")
    print("="*60)

    manager = WorkerManager()

    # Pause a worker
    print("\n1. Pausing worker...")
    result = manager.pause_worker(1, "urgency")
    print(f"   Result: {result['status']}")

    # Wait a bit
    time.sleep(2)

    # Resume a worker
    print("\n2. Resuming worker...")
    result = manager.resume_worker(1, "urgency")
    print(f"   Result: {result['status']}")

    # Stop a worker
    print("\n3. Stopping worker...")
    result = manager.stop_worker(1, "urgency", timeout=30)
    print(f"   Result: {result['status']}")
    print(f"   Exit code: {result.get('exit_code', 'N/A')}")
    print(f"   Forced: {result.get('forced', False)}")


def example_stop_all():
    """Example: Stop all workers."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Stop All Workers")
    print("="*60)

    manager = WorkerManager()

    # Stop all workers
    result = manager.stop_all_workers(timeout=30)

    print(f"\nStopped: {result['stopped']} workers")
    print(f"Forced: {result['forced']} workers")


def interactive_menu():
    """Interactive menu for demonstrating worker management."""
    manager = WorkerManager()

    while True:
        print("\n" + "="*60)
        print("WORKER MANAGER - INTERACTIVE DEMO")
        print("="*60)
        print("\n1. Start single worker (Annotator 1, Urgency)")
        print("2. Start all enabled workers")
        print("3. Monitor specific worker")
        print("4. Monitor all workers")
        print("5. Pause worker")
        print("6. Resume worker")
        print("7. Stop worker")
        print("8. Stop all workers")
        print("9. Exit")

        choice = input("\nEnter choice (1-9): ").strip()

        if choice == '1':
            example_start_single_worker()

        elif choice == '2':
            example_start_all_enabled()

        elif choice == '3':
            example_monitor_progress()

        elif choice == '4':
            example_monitor_all()

        elif choice == '5':
            result = manager.pause_worker(1, "urgency")
            print(f"\nResult: {result['status']}")

        elif choice == '6':
            result = manager.resume_worker(1, "urgency")
            print(f"\nResult: {result['status']}")

        elif choice == '7':
            result = manager.stop_worker(1, "urgency")
            print(f"\nResult: {result['status']}")

        elif choice == '8':
            example_stop_all()

        elif choice == '9':
            print("\nExiting...")
            break

        else:
            print("\nInvalid choice. Please enter 1-9.")

        input("\nPress Enter to continue...")


def main():
    """Main function."""
    print("\n" + "="*60)
    print("WORKER MANAGER EXAMPLE USAGE")
    print("="*60)
    print("\nThis script demonstrates worker management capabilities.")
    print("\nOptions:")
    print("1. Run all examples in sequence")
    print("2. Interactive menu")
    print("3. Exit")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == '1':
        # Run all examples
        print("\nRunning all examples...\n")

        # Note: These are just demonstrations
        # In real usage, you would not run all of these in sequence
        # as they would interfere with each other

        print("\nNOTE: These are example function definitions.")
        print("To actually run them, uncomment the desired function calls below.")
        print("Running all in sequence may cause conflicts.\n")

        # Uncomment to run specific examples:
        # example_start_single_worker()
        # example_monitor_progress()
        # example_monitor_all()
        # example_control_workers()

    elif choice == '2':
        interactive_menu()

    elif choice == '3':
        print("\nExiting...")

    else:
        print("\nInvalid choice.")


if __name__ == "__main__":
    main()
