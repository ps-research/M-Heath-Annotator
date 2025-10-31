"""
Test script for Gemini API connection and key validity.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.annotator import GeminiAnnotator
from backend.core.parser import ResponseParser
from backend.utils.file_operations import atomic_read_json


def test_api_key(annotator_id: int, api_key: str):
    """Test a single API key."""
    print(f"\n{'='*60}")
    print(f"Testing Annotator {annotator_id}")
    print(f"{'='*60}")

    if not api_key or api_key.strip() == "":
        print(f"❌ No API key configured")
        return False

    try:
        # Create annotator
        gemini = GeminiAnnotator(api_key, "gemini-2.0-flash-exp")

        # Test simple prompt
        test_prompt = "Say exactly this: <<TEST_RESPONSE>>"
        print(f"📤 Sending test prompt...")

        response_text, error = gemini.generate(test_prompt)

        if error:
            print(f"❌ API Error: {error}")
            return False

        print(f"✅ API call successful!")
        print(f"📥 Response preview: {response_text[:100]}...")

        # Test parsing
        parser = ResponseParser()

        # Test urgency parsing
        urgency_response = "<<LEVEL_2>>"
        label, parse_err, valid_err = parser.parse_response(urgency_response, "urgency")

        if label == "LEVEL_2":
            print(f"✅ Parser working correctly")
        else:
            print(f"⚠️  Parser issue: {parse_err or valid_err}")

        return True

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False


def main():
    """Test all configured API keys."""
    print("\n" + "="*60)
    print("GEMINI API CONNECTION TEST")
    print("="*60)

    # Load API keys
    base_dir = Path(__file__).parent.parent
    api_keys_path = base_dir / "config" / "api_keys.json"

    api_keys = atomic_read_json(str(api_keys_path))

    if not api_keys:
        print(f"\n❌ Could not load API keys from {api_keys_path}")
        return

    # Test each annotator
    results = {}

    for annotator_id in [1, 2, 3, 4, 5]:
        key = f"annotator_{annotator_id}"
        api_key = api_keys.get(key, "")

        success = test_api_key(annotator_id, api_key)
        results[annotator_id] = success

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    for annotator_id, success in results.items():
        status = "✅ Working" if success else "❌ Failed"
        print(f"Annotator {annotator_id}: {status}")

    print()


if __name__ == "__main__":
    main()
