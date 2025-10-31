"""
Response parser for extracting labels from LLM responses.
"""

import re
import json
from typing import Tuple, Optional


class ResponseParser:
    """
    Parses LLM responses and extracts labels using << >> tags.

    Validates labels according to domain-specific rules.
    """

    @staticmethod
    def parse_response(response_text: str, domain: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse response and extract label.

        Args:
            response_text: Full LLM response
            domain: Domain name

        Returns:
            Tuple of (label, parsing_error, validity_error)
            - Success: (label, None, None)
            - Parsing error: (None, error_message, None)
            - Validity error: (None, None, error_message)
        """
        # Extract content from << >> tags
        match = re.search(r'<<(.+?)>>', response_text, re.DOTALL)

        if not match:
            return (None, "Could not find << >> tags in response", None)

        raw_label = match.group(1).strip()

        # Domain-specific validation
        if domain == "urgency":
            return ResponseParser._parse_urgency(raw_label)

        elif domain == "therapeutic":
            return ResponseParser._parse_therapeutic(raw_label)

        elif domain == "intensity":
            return ResponseParser._parse_intensity(raw_label)

        elif domain == "adjunct":
            return ResponseParser._parse_adjunct(raw_label)

        elif domain == "modality":
            return ResponseParser._parse_modality(raw_label)

        elif domain == "redressal":
            return ResponseParser._parse_redressal(raw_label)

        else:
            return (None, None, f"Unknown domain: {domain}")

    @staticmethod
    def _parse_urgency(raw_label: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse urgency level (LEVEL_0 to LEVEL_4)."""
        # Search for LEVEL pattern (case insensitive, flexible spacing)
        match = re.search(r'LEVEL[_\s]*([0-4])', raw_label, re.IGNORECASE)

        if match:
            digit = match.group(1)
            label = f"LEVEL_{digit}"
            return (label, None, None)
        else:
            return (None, None, f"Invalid urgency format: {raw_label}")

    @staticmethod
    def _parse_therapeutic(raw_label: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse therapeutic approaches (multi-label: TA-1 to TA-9)."""
        # Find all TA-X codes
        codes = re.findall(r'TA-([1-9])', raw_label)

        if codes:
            # Sort and deduplicate
            unique_codes = sorted(set(codes), key=lambda x: int(x))
            label = ", ".join([f"TA-{c}" for c in unique_codes])
            return (label, None, None)
        else:
            return (None, None, f"No valid TA codes found: {raw_label}")

    @staticmethod
    def _parse_intensity(raw_label: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse intensity level (INT-1 to INT-5)."""
        # Search for INT pattern
        match = re.search(r'INT-([1-5])', raw_label, re.IGNORECASE)

        if match:
            digit = match.group(1)
            label = f"INT-{digit}"
            return (label, None, None)
        else:
            return (None, None, f"Invalid intensity format: {raw_label}")

    @staticmethod
    def _parse_adjunct(raw_label: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse adjunct services (multi-label: ADJ-1 to ADJ-8, or NONE)."""
        # Check for NONE
        if "NONE" in raw_label.upper():
            return ("NONE", None, None)

        # Find all ADJ-X codes
        codes = re.findall(r'ADJ-([1-8])', raw_label)

        if codes:
            # Sort and deduplicate
            unique_codes = sorted(set(codes), key=lambda x: int(x))
            label = ", ".join([f"ADJ-{c}" for c in unique_codes])
            return (label, None, None)
        else:
            return (None, None, f"No valid ADJ codes found: {raw_label}")

    @staticmethod
    def _parse_modality(raw_label: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse treatment modality (multi-label: MOD-1 to MOD-6)."""
        # Find all MOD-X codes
        codes = re.findall(r'MOD-([1-6])', raw_label)

        if codes:
            # Sort and deduplicate
            unique_codes = sorted(set(codes), key=lambda x: int(x))
            label = ", ".join([f"MOD-{c}" for c in unique_codes])
            return (label, None, None)
        else:
            return (None, None, f"No valid MOD codes found: {raw_label}")

    @staticmethod
    def _parse_redressal(raw_label: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse redressal points (JSON array of strings)."""
        try:
            # Try to parse as JSON
            points = json.loads(raw_label)

            # Validate it's a list
            if not isinstance(points, list):
                return (None, None, f"Invalid redressal format (not a list): {raw_label}")

            # Validate all elements are strings
            if not all(isinstance(p, str) for p in points):
                return (None, None, f"Invalid redressal format (not all strings): {raw_label}")

            # Validate count
            if len(points) < 2:
                return (None, None, f"Too few redressal points (minimum 2): {raw_label}")

            if len(points) > 10:
                return (None, None, f"Too many redressal points (maximum 10): {raw_label}")

            # Return as JSON string
            label = json.dumps(points)
            return (label, None, None)

        except json.JSONDecodeError as e:
            return (None, None, f"Invalid JSON in redressal points: {str(e)}")
