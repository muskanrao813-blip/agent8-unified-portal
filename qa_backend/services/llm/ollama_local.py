"""Ollama-based local LLM implementation (runs locally, no API key needed)."""

import json
import logging
from typing import Dict, List
from app.services.llm.base import LLMProvider
from app.services.llm.prompts import format_rubric_prompt

logger = logging.getLogger(__name__)

# Lazy import to defer until needed
_ollama_client = None

def _get_ollama_client():
    """Lazy load Ollama client."""
    global _ollama_client
    if _ollama_client is not None:
        return _ollama_client

    try:
        from ollama import Client
        logger.info("Connecting to Ollama on localhost:11434...")
        _ollama_client = Client(host='http://localhost:11434')
        # Test connection
        _ollama_client.list()
        logger.info("Ollama client connected successfully")
        return _ollama_client
    except Exception as e:
        logger.error(f"Error connecting to Ollama: {e}")
        logger.error("Make sure Ollama is running: ollama serve")
        raise


class OllamaLocalProvider(LLMProvider):
    """Local LLM provider using Ollama (Mistral/Llama/etc)."""

    def __init__(self, model_name: str = "mistral"):
        """Initialize with model name.

        Available models (download with: ollama pull <model>):
        - mistral (7B, fast, good quality)
        - neural-chat (7B, optimized for chat)
        - llama2 (7B, slower but decent)
        - dolphin-mixtral (8x7B, very good but slow)
        """
        self.model_name = model_name
        self.client = None

    def _get_client(self):
        """Get or initialize Ollama client."""
        if self.client is None:
            self.client = _get_ollama_client()
        return self.client

    def analyze_all_dimensions(
        self,
        transcript_segments: List[Dict],
        metrics: Dict,
        call_id: str,
        dietician_name: str,
        patient_id: str
    ) -> Dict:
        """Analyze call quality using local Ollama model."""
        try:
            client = self._get_client()

            # Format transcript
            transcript_text = self._format_transcript(transcript_segments)

            # Build prompt
            prompt = format_rubric_prompt(transcript_text, metrics)

            # Call Ollama
            logger.info(f"Analyzing call {call_id} with {self.model_name}...")
            response = client.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False,
                format='json',
            )

            response_text = response['response'].strip()

            # Parse JSON response
            result = json.loads(response_text)

            logger.info(f"Analysis complete for call {call_id}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama response as JSON: {e}")
            logger.error(f"Response: {response_text[:500]}")
            # Return default response if parsing fails
            return self._default_response()
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
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

    def _default_response(self) -> Dict:
        """Return default response structure if LLM fails."""
        return {
            "dimension_scores": {
                "discovery_assessment": {
                    "score": 5,
                    "evidence": ["Unable to analyze - LLM processing error"],
                    "sub_criteria_met": {},
                    "red_flag_detected": False,
                    "handled_appropriately": False,
                },
                "empathy_communication": {
                    "score": 5,
                    "evidence": ["Unable to analyze - LLM processing error"],
                    "sub_criteria_met": {},
                    "red_flag_detected": False,
                    "handled_appropriately": False,
                },
                "rushed_forced_detection": {
                    "score": 5,
                    "evidence": ["Unable to analyze - LLM processing error"],
                    "sub_criteria_met": {},
                    "red_flag_detected": False,
                    "handled_appropriately": False,
                },
                "adherence_counselling": {
                    "score": 5,
                    "evidence": ["Unable to analyze - LLM processing error"],
                    "sub_criteria_met": {},
                    "red_flag_detected": False,
                    "handled_appropriately": False,
                },
                "consultation_completeness": {
                    "score": 5,
                    "evidence": ["Unable to analyze - LLM processing error"],
                    "sub_criteria_met": {},
                    "red_flag_detected": False,
                    "handled_appropriately": False,
                },
            },
            "overall_notes": "LLM analysis failed - check Ollama service"
        }
