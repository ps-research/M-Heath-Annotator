"""
Dataset loader for Excel source file with caching.
"""

import os
from pathlib import Path
from typing import Optional, Dict
import pandas as pd


class DatasetLoader:
    """
    Loads and caches the source dataset from Excel file.

    Provides efficient access to samples by index or ID.
    """

    def __init__(self, source_path: str):
        """
        Initialize dataset loader.

        Args:
            source_path: Path to Excel file
        """
        self.source_path = Path(source_path)
        self.dataset: Optional[pd.DataFrame] = None
        self.loaded = False

    def load(self) -> pd.DataFrame:
        """
        Load dataset from Excel file with validation.

        Returns:
            Loaded DataFrame

        Raises:
            FileNotFoundError: If source file doesn't exist
            ValueError: If required columns are missing
        """
        # Return cached dataset if already loaded
        if self.loaded and self.dataset is not None:
            return self.dataset

        # Check if file exists
        if not self.source_path.exists():
            raise FileNotFoundError(
                f"Dataset file not found: {self.source_path}\n"
                f"Please place your Excel file at this location."
            )

        try:
            # Load Excel file
            print(f"Loading dataset from {self.source_path}...")
            self.dataset = pd.read_excel(self.source_path)

            # Validate required columns exist
            required_columns = ['ID', 'Text']
            missing_columns = [col for col in required_columns if col not in self.dataset.columns]

            if missing_columns:
                raise ValueError(
                    f"Missing required columns: {missing_columns}\n"
                    f"Dataset must have columns: {required_columns}"
                )

            # Convert ID to string
            self.dataset['ID'] = self.dataset['ID'].astype(str)

            # Convert Text to string and handle NaN
            self.dataset['Text'] = self.dataset['Text'].astype(str)

            # Remove rows with missing ID or Text
            original_count = len(self.dataset)
            self.dataset = self.dataset[
                (self.dataset['ID'].notna()) &
                (self.dataset['ID'] != 'nan') &
                (self.dataset['Text'].notna()) &
                (self.dataset['Text'] != 'nan') &
                (self.dataset['Text'].str.strip() != '')
            ]

            removed_count = original_count - len(self.dataset)
            if removed_count > 0:
                print(f"Removed {removed_count} rows with missing ID or Text")

            # Reset index
            self.dataset = self.dataset.reset_index(drop=True)

            self.loaded = True
            print(f"✅ Loaded {len(self.dataset)} samples from dataset")

            return self.dataset

        except Exception as e:
            raise Exception(f"Failed to load dataset: {str(e)}")

    def get_sample_by_index(self, index: int) -> Optional[Dict[str, str]]:
        """
        Get sample by numeric index.

        Args:
            index: Row index (0-based)

        Returns:
            Dictionary with 'id' and 'text' keys, or None if invalid index
        """
        # Ensure dataset is loaded
        if not self.loaded:
            self.load()

        # Check if index is valid
        if index < 0 or index >= len(self.dataset):
            return None

        try:
            row = self.dataset.iloc[index]
            return {
                "id": row['ID'],
                "text": row['Text']
            }
        except Exception as e:
            print(f"Error getting sample at index {index}: {str(e)}")
            return None

    def get_sample_by_id(self, sample_id: str) -> Optional[Dict[str, str]]:
        """
        Get sample by ID.

        Args:
            sample_id: Sample ID to look up

        Returns:
            Dictionary with 'id' and 'text' keys, or None if not found
        """
        # Ensure dataset is loaded
        if not self.loaded:
            self.load()

        try:
            # Filter by ID
            matches = self.dataset[self.dataset['ID'] == sample_id]

            if len(matches) == 0:
                return None

            row = matches.iloc[0]
            return {
                "id": row['ID'],
                "text": row['Text']
            }
        except Exception as e:
            print(f"Error getting sample by ID {sample_id}: {str(e)}")
            return None

    def get_total_count(self) -> int:
        """
        Get total number of samples in dataset.

        Returns:
            Number of samples
        """
        # Ensure dataset is loaded
        if not self.loaded:
            self.load()

        return len(self.dataset)
