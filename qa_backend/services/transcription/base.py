from abc import ABC, abstractmethod
from typing import List, Dict


class Segment(dict):
    """Diarized transcript segment."""
    pass


class TranscriptionProvider(ABC):
    """Abstract base class for transcription providers."""

    @abstractmethod
    def transcribe(self, audio_path: str) -> List[Segment]:
        """
        Transcribe audio file and return diarized segments.

        Returns:
            List of segments: [{"speaker": str, "text": str, "start_s": float, "end_s": float}, ...]
        """
        pass

    @abstractmethod
    def get_raw_response(self) -> Dict:
        """Get the raw provider response for audit purposes."""
        pass
