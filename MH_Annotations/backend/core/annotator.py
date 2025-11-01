"""
Gemini API client wrapper for annotation.
"""

import os
from typing import Tuple, Optional
from google import genai
from google.genai import types


class GeminiAnnotator:
    """
    Wrapper for Gemini API client with error handling.

    Provides streaming generation with comprehensive error detection.

    NEW: Supports debug mode via GEMINI_DEBUG environment variable.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini client.

        Args:
            api_key: Gemini API key
            model_name: Model identifier

        Raises:
            ValueError: If API key is empty
        """
        if not api_key or api_key.strip() == "":
            raise ValueError("API key cannot be empty")

        self.api_key = api_key
        self.model_name = model_name

        # Initialize Gemini client
        self.client = genai.Client(api_key=api_key)

        # NEW: Debug mode support
        from backend.core.logger_config import get_logger
        self.logger = get_logger("gemini_api")
        self.debug_mode = os.getenv("GEMINI_DEBUG", "false").lower() == "true"

        if self.debug_mode:
            self.logger.info("🔍 Gemini API Debug Mode ENABLED")

    def generate(self, prompt: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate response from Gemini API.

        NEW: Logs full request/response if GEMINI_DEBUG=true.

        Args:
            prompt: Input prompt

        Returns:
            Tuple of (response_text, error_type)
            - Success: (response_text, None)
            - Error: (None, error_type)

            Error types:
            - "RATE_LIMIT": API rate limit hit
            - "INVALID_KEY": Invalid API key
            - "API_ERROR: {message}": Other API errors
        """
        # NEW: Log prompt if debug mode
        if self.debug_mode:
            self.logger.debug("="*70)
            self.logger.debug("📤 SENDING TO GEMINI API:")
            self.logger.debug(f"   Model: {self.model_name}")
            self.logger.debug(f"   Prompt length: {len(prompt)} chars")
            self.logger.debug(f"   Prompt preview: {prompt[:200]}...")
            if len(prompt) <= 1000:
                self.logger.debug(f"\n   Full prompt:\n{prompt}")
            self.logger.debug("="*70)

        try:
            # Create contents structure
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                )
            ]

            # Create config
            config = types.GenerateContentConfig()

            # Call streaming API
            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=config
            ):
                # Handle None chunks
                if chunk.text:
                    response_text += chunk.text

            # NEW: Log response if debug mode
            if self.debug_mode:
                self.logger.debug("="*70)
                self.logger.debug("📥 RECEIVED FROM GEMINI API:")
                self.logger.debug(f"   Response length: {len(response_text)} chars")
                self.logger.debug(f"   Response: {response_text}")
                self.logger.debug("="*70)

            # Return success
            return (response_text, None)

        except Exception as e:
            # NEW: Always log errors
            self.logger.error(f"❌ Gemini API Error: {str(e)}")

            error_str = str(e).lower()

            # Check for rate limit errors
            if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                self.logger.error("   Error type: RATE_LIMIT")
                return (None, "RATE_LIMIT")

            # Check for authentication errors
            if "403" in error_str or "permission" in error_str or "api key" in error_str:
                self.logger.error("   Error type: INVALID_KEY")
                return (None, "INVALID_KEY")

            # Check for invalid API key
            if "invalid" in error_str and "key" in error_str:
                self.logger.error("   Error type: INVALID_KEY")
                return (None, "INVALID_KEY")

            # Other API errors
            self.logger.error(f"   Error type: API_ERROR")
            return (None, f"API_ERROR: {str(e)}")
