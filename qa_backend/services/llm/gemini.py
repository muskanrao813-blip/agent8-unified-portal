"""Gemini Flash implementation for rubric analysis."""

import json
import logging
import os
from typing import Dict, List
from app.services.llm.base import LLMProvider
from app.services.llm.prompts import SYSTEM_PROMPT, format_rubric_prompt

logger = logging.getLogger(__name__)

# Lazy import to handle Python 3.14 compatibility
_genai = None
_genai_error = None

def _get_genai():
    """Lazy load genai to avoid import errors at startup."""
    global _genai, _genai_error
    if _genai is not None:
        return _genai
    if _genai_error is not None:
        raise _genai_error

    try:
        import google.generativeai as genai
        _genai = genai
        return _genai
    except Exception as e:
        _genai_error = e
        raise


class GeminiLLMProvider(LLMProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        self._model = None

    @property
    def model(self):
        """Lazy load Gemini model."""
        if self._model is None:
            genai = _get_genai()
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(
                "gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT,
            )
        return self._model

    def analyze_all_dimensions(
        self,
        transcript_segments: List[Dict],
        metrics: Dict,
        call_id: str,
        dietician_name: str,
        patient_id: str
    ) -> Dict:
        """Analyze all dimensions with Gemini Flash."""
        try:
            # Format transcript for prompt
            transcript_text = self._format_transcript(transcript_segments)

            # Format rubric prompt with metrics
            rubric_prompt = format_rubric_prompt(transcript_text, metrics)

            # Call Gemini with response schema
            response = self.model.generate_content(
                rubric_prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                    max_output_tokens=4096,
                ),
            )

            # Parse response
            response_text = response.text
            result = json.loads(response_text)

            logger.info(f"Successfully analyzed call {call_id}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}\nResponse: {response_text}")
            raise
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise

    def _format_transcript(self, segments: List[Dict]) -> str:
        """Format diarized segments into readable transcript."""
        lines = []
        for seg in segments:
            speaker = seg.get("speaker", "Unknown").replace("_", " ").title()
            text = seg.get("text", "")
            timestamp = seg.get("start_s", 0)
            lines.append(f"[{timestamp:.1f}s] {speaker}: {text}")

        return "\n".join(lines)
