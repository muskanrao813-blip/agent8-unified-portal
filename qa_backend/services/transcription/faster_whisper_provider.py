"""Faster-Whisper implementation for optimized speech-to-text."""

import logging
import os
from typing import List, Dict
from app.services.transcription.base import TranscriptionProvider, Segment

logger = logging.getLogger(__name__)

class FasterWhisperProvider(TranscriptionProvider):
    """Speech-to-text using faster-whisper (4x faster than Whisper)."""

    def __init__(self):
        self.raw_response = None
        self.model = None

    def transcribe(self, audio_path: str) -> List[Segment]:
        """Transcribe audio using faster-whisper."""
        try:
            from faster_whisper import WhisperModel
            import ssl

            logger.info(f"[FasterWhisper] Transcribing {audio_path}")

            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            # Load tiny model (fastest, CPU-efficient)
            logger.info("[FasterWhisper] Loading tiny model...")
            # Disable SSL verification for model download
            ssl._create_default_https_context = ssl._create_unverified_context
            model = WhisperModel("tiny", device="cpu", compute_type="int8")

            # Transcribe with language hint for Hindi
            logger.info("[FasterWhisper] Starting transcription...")
            segments, info = model.transcribe(
                audio_path,
                language="hi",  # Hindi/Hinglish
                beam_size=5,
                condition_on_previous_text=False,
            )

            logger.info(f"[FasterWhisper] Detected language: {info.language}")

            # Convert to our Segment format
            result_segments = []
            for seg in segments:
                result_segments.append({
                    'speaker': 'speaker_0',  # faster-whisper doesn't do diarization
                    'text': seg.text,
                    'start_s': round(seg.start, 2),
                    'end_s': round(seg.end, 2),
                })

            self.raw_response = {
                'segments': result_segments,
                'language': info.language,
            }

            logger.info(f"[FasterWhisper] Complete - {len(result_segments)} segments")
            return self._extract_segments({'segments': result_segments})

        except Exception as e:
            logger.error(f"[FasterWhisper] Error: {type(e).__name__}: {e}")
            raise

    def _extract_segments(self, result: Dict) -> List[Segment]:
        """Extract segments from transcription result."""
        segments = []
        for idx, seg in enumerate(result.get('segments', [])):
            segment = Segment({
                'speaker': seg.get('speaker', 'speaker_0'),
                'text': seg.get('text', '').strip(),
                'start_s': seg.get('start_s', 0),
                'end_s': seg.get('end_s', 0),
            })
            if segment.get('text'):
                segments.append(segment)

        return segments

    def get_raw_response(self) -> Dict:
        """Return raw response for audit."""
        return self.raw_response or {}
