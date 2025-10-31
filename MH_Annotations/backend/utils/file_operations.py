"""
File operations utilities with atomic writes to prevent corruption.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any


def atomic_write_json(data: Dict[Any, Any], filepath: str) -> None:
    """
    Atomically write JSON data to a file using temporary file and rename.

    This prevents file corruption if the process is interrupted during writing.

    Args:
        data: Dictionary to write as JSON
        filepath: Target file path

    Raises:
        Exception: If write operation fails
    """
    filepath = Path(filepath)
    dirname = filepath.parent

    # Ensure directory exists
    ensure_directory(str(dirname))

    temp_file = None
    try:
        # Create temporary file in same directory
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=dirname,
            delete=False,
            prefix='.tmp_',
            suffix='.json'
        ) as f:
            temp_file = f.name
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk

        # Atomic rename
        os.replace(temp_file, filepath)

    except Exception as e:
        # Clean up temp file if operation failed
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        raise Exception(f"Failed to write {filepath}: {str(e)}")


def atomic_read_json(filepath: str) -> Optional[Dict[Any, Any]]:
    """
    Read JSON data from file.

    Args:
        filepath: Path to JSON file

    Returns:
        Parsed dictionary or None if file doesn't exist or is invalid
    """
    filepath = Path(filepath)

    # Check if file exists
    if not filepath.exists():
        return None

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data

    except FileNotFoundError:
        return None

    except json.JSONDecodeError as e:
        print(f"Warning: JSON decode error in {filepath}: {str(e)}")
        return None

    except Exception as e:
        print(f"Error reading {filepath}: {str(e)}")
        raise


def ensure_directory(path: str) -> None:
    """
    Create directory and all parent directories if they don't exist.

    Args:
        path: Directory path to create
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        print(f"Permission error creating directory {path}: {str(e)}")
        raise
    except OSError as e:
        print(f"OS error creating directory {path}: {str(e)}")
        raise
