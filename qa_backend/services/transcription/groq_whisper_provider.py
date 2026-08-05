"""Groq Whisper API provider for fast, free speech-to-text."""

import logging
import os
from typing import List, Dict
from app.services.transcription.base import TranscriptionProvider, Segment

logger = logging.getLogger(__name__)

class GroqWhisperProvider(TranscriptionProvider):
    """Speech-to-text using Groq's Whisper API (fast, free tier available)."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.raw_response = None
        if not self.api_key:
            logger.error("GROQ_API_KEY not set in environment or parameters")
            raise ValueError("GROQ_API_KEY not set. Set via GROQ_API_KEY environment variable.")

    def transcribe(self, audio_path: str) -> List[Segment]:
        """Transcribe audio using Groq Whisper API."""
        try:
            from groq import Groq
            import httpx

            logger.info(f"[GroqWhisper] Transcribing {audio_path}")

            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            # Initialize Groq client with SSL verification disabled
            http_client = httpx.Client(verify=False)
            client = Groq(api_key=self.api_key, http_client=http_client)

            # Read audio file
            logger.info("[GroqWhisper] Reading audio file...")
            with open(audio_path, "rb") as f:
                audio_data = f.read()

            logger.info(f"[GroqWhisper] Audio file size: {len(audio_data)} bytes")

            # Transcribe with Groq
            logger.info("[GroqWhisper] Calling Groq Whisper API...")
            with open(audio_path, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    file=(os.path.basename(audio_path), f, "audio/mpeg"),
                    model="whisper-large-v3-turbo",
                    language="hi",  # Hindi
                    temperature=0.0,
                )

            transcription_text = transcript.text
            logger.info(f"[GroqWhisper] Transcription received: {len(transcription_text)} chars")
            logger.info(f"[GroqWhisper] Text: {transcription_text[:200]}")

            # Store raw response
            self.raw_response = {
                'text': transcription_text,
                'language': 'hi',
                'model': 'whisper-large-v3-turbo',
            }

            # Return as single segment (Groq doesn't provide timestamps)
            segments = [Segment({
                'speaker': 'speaker_0',
                'text': transcription_text,
                'start_s': 0,
                'end_s': 0,  # Groq doesn't provide duration
            })]

            logger.info(f"[GroqWhisper] Complete - {len(transcription_text)} chars")
            return segments

        except Exception as e:
            logger.error(f"[GroqWhisper] Error: {type(e).__name__}: {e}")
            raise

    def get_raw_response(self) -> Dict:
        """Return raw response for audit."""
        return self.raw_response or {}
