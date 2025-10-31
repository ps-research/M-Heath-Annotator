"""
Test script for single worker process with small dataset.

NOTE: This requires:
1. A valid API key configured for annotator 1
2. A test dataset at data/source/m_help_dataset.xlsx
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.worker import AnnotationWorker
from backend.core.progress_logger import ProgressLogger
from backend.utils.file_operations import atomic_read_json


def check_prerequisites():
    """Check if prerequisites are met."""
    base_dir = Path(__file__).parent.parent

    # Check API key
    api_keys_path = base_dir / "config" / "api_keys.json"
    api_keys = atomic_read_json(str(api_keys_path))

    if not api_keys or not api_keys.get("annotator_1"):
        print("❌ No API key configured for annotator 1")
        print("   Please add your API key to config/api_keys.json")
        return False

    # Check dataset
    dataset_path = base_dir / "data" / "source" / "m_help_dataset.xlsx"
    if not dataset_path.exists():
        print("❌ Dataset not found at data/source/m_help_dataset.xlsx")
        print("   Please place your test dataset at this location")
        return False

    # Check settings
    settings_path = base_dir / "config" / "settings.json"
    settings = atomic_read_json(str(settings_path))

    if not settings:
        print("❌ Settings not found")
        return False

    # Check if enabled
    annotator1_settings = settings["annotators"]["1"]["urgency"]
    if not annotator1_settings["enabled"]:
        print("⚠️  Annotator 1, urgency domain is disabled in settings")
        print("   Temporarily enabling for test...")

        settings["annotators"]["1"]["urgency"]["enabled"] = True
        settings["annotators"]["1"]["urgency"]["target_count"] = 5

        from backend.utils.file_operations import atomic_write_json
        atomic_write_json(settings, str(settings_path))

    return True


def test_worker():
    """Test worker with small dataset."""
    print("\n" + "="*60)
    print("SINGLE WORKER TEST")
    print("="*60)

    # Check prerequisites
    if not check_prerequisites():
        return False

    try:
        print("\n🚀 Starting worker...")
        print("   Annotator: 1")
        print("   Domain: urgency")
        print("   Target: 5 samples\n")

        # Create and run worker
        worker = AnnotationWorker(1, "urgency")
        worker.run()

        # Check results
        print("\n" + "="*60)
        print("VERIFICATION")
        print("="*60)

        logger = ProgressLogger(1, "urgency")
        progress = logger.load()

        print(f"\n✅ Status: {progress['status']}")
        print(f"✅ Completed: {len(progress['completed_ids'])} samples")
        print(f"⚠️  Malformed: {len(progress['malformed_ids'])} samples")

        # Check annotations file
        base_dir = Path(__file__).parent.parent
        annotations_file = base_dir / "data" / "annotations" / "annotator_1" / "urgency" / "annotations.jsonl"

        if annotations_file.exists():
            with open(annotations_file, 'r') as f:
                lines = f.readlines()
            print(f"✅ Annotations saved: {len(lines)} lines in JSONL file")
        else:
            print(f"❌ Annotations file not found")
            return False

        # Display first annotation
        if lines:
            import json
            first_annotation = json.loads(lines[0])
            print(f"\n📝 First annotation:")
            print(f"   ID: {first_annotation['id']}")
            print(f"   Label: {first_annotation['label']}")
            print(f"   Malformed: {first_annotation['malformed']}")

        print("\n✅ Worker test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Worker test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_resume():
    """Test resume from checkpoint."""
    print("\n" + "="*60)
    print("RESUME TEST")
    print("="*60)

    try:
        # Modify progress to simulate incomplete work
        logger = ProgressLogger(1, "urgency")
        progress = logger.load()

        original_count = len(progress['completed_ids'])

        if original_count < 3:
            print("⚠️  Not enough completed samples for resume test")
            return True

        # Remove last 2 completed IDs
        progress['completed_ids'] = progress['completed_ids'][:-2]
        progress['status'] = "stopped"
        logger.save(progress)

        print(f"🔄 Simulated incomplete work (removed 2 completed samples)")
        print(f"   Completed: {len(progress['completed_ids'])} samples")

        # Run worker again
        print("\n🚀 Resuming worker...\n")

        worker = AnnotationWorker(1, "urgency")
        worker.run()

        # Verify
        progress = logger.load()
        new_count = len(progress['completed_ids'])

        print(f"\n✅ After resume: {new_count} samples completed")

        if new_count >= original_count:
            print("✅ Resume test passed!")
            return True
        else:
            print("❌ Resume test failed (did not complete expected samples)")
            return False

    except Exception as e:
        print(f"\n❌ Resume test failed: {str(e)}")
        return False


def main():
    """Run worker tests."""
    print("\n" + "="*70)
    print("WORKER TESTING SUITE")
    print("="*70)
    print("\nThis will:")
    print("1. Test basic worker functionality with 5 samples")
    print("2. Test resume from checkpoint")
    print("\nNOTE: Requires valid API key and test dataset")
    print("="*70)

    # Run basic worker test
    worker_success = test_worker()

    if not worker_success:
        print("\n❌ Basic worker test failed, skipping resume test")
        return

    # Run resume test
    resume_success = test_resume()

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Basic Worker Test: {'✅ PASSED' if worker_success else '❌ FAILED'}")
    print(f"Resume Test: {'✅ PASSED' if resume_success else '❌ FAILED'}")

    if worker_success and resume_success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed")

    print()


if __name__ == "__main__":
    main()
