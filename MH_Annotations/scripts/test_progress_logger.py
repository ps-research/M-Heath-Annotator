"""
Test script for progress logger functionality.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.progress_logger import ProgressLogger


def test_basic_operations():
    """Test basic progress logger operations."""
    print("\n" + "="*60)
    print("TEST: Basic Progress Logger Operations")
    print("="*60)

    try:
        # Create logger
        logger = ProgressLogger(1, "urgency")
        print("✅ Created progress logger")

        # Load progress
        progress = logger.load()
        print(f"✅ Loaded progress: {progress['status']}")

        # Add completed samples
        logger.add_completed("sample_001", "LEVEL_2", malformed=False)
        logger.add_completed("sample_002", "LEVEL_3", malformed=False)
        logger.add_completed("sample_003", "MALFORMED", malformed=True)
        print("✅ Added completed samples")

        # Check counts
        completed_count = logger.get_completed_count()
        assert completed_count == 2, f"Expected 2 completed, got {completed_count}"
        print(f"✅ Completed count: {completed_count}")

        # Check malformed
        progress = logger.load()
        malformed_count = len(progress['malformed_ids'])
        assert malformed_count == 1, f"Expected 1 malformed, got {malformed_count}"
        print(f"✅ Malformed count: {malformed_count}")

        # Update status
        logger.update_status("running")
        progress = logger.load()
        assert progress['status'] == "running"
        print(f"✅ Status updated: {progress['status']}")

        # Update speed
        logger.update_speed(10, 60)  # 10 samples in 60 seconds = 10 per minute
        progress = logger.load()
        speed = progress['stats']['samples_per_min']
        assert speed == 10.0, f"Expected speed 10.0, got {speed}"
        print(f"✅ Speed updated: {speed} samples/min")

        # Test is_complete
        progress['target_count'] = 2
        logger.save(progress)
        is_complete = logger.is_complete()
        assert is_complete, "Should be complete with 2 completed and target 2"
        print(f"✅ Completion check works")

        # Test staleness
        is_stale = logger.is_stale(minutes=5)
        assert not is_stale, "Should not be stale (just updated)"
        print(f"✅ Staleness check works")

        print("\n✅ All basic operations passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_persistence():
    """Test that progress persists across instances."""
    print("\n" + "="*60)
    print("TEST: Progress Persistence")
    print("="*60)

    try:
        # Create first logger and add data
        logger1 = ProgressLogger(2, "therapeutic")
        logger1.add_completed("sample_A", "TA-1, TA-2", malformed=False)
        print("✅ Added data with first logger")

        # Create second logger and verify data persists
        logger2 = ProgressLogger(2, "therapeutic")
        progress = logger2.load()

        assert "sample_A" in progress['completed_ids'], "Data should persist"
        print("✅ Data persisted across logger instances")

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False


def test_error_handling():
    """Test error handling."""
    print("\n" + "="*60)
    print("TEST: Error Handling")
    print("="*60)

    try:
        # Test invalid annotator ID
        try:
            logger = ProgressLogger(999, "urgency")
            print("❌ Should have raised ValueError for invalid annotator ID")
            return False
        except ValueError:
            print("✅ Correctly rejected invalid annotator ID")

        # Test invalid domain
        try:
            logger = ProgressLogger(1, "invalid_domain")
            print("❌ Should have raised ValueError for invalid domain")
            return False
        except ValueError:
            print("✅ Correctly rejected invalid domain")

        # Test invalid status
        logger = ProgressLogger(3, "intensity")
        try:
            logger.update_status("invalid_status")
            print("❌ Should have raised ValueError for invalid status")
            return False
        except ValueError:
            print("✅ Correctly rejected invalid status")

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("PROGRESS LOGGER TEST SUITE")
    print("="*60)

    results = []

    # Run tests
    results.append(("Basic Operations", test_basic_operations()))
    results.append(("Persistence", test_persistence()))
    results.append(("Error Handling", test_error_handling()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed")

    print()


if __name__ == "__main__":
    main()
