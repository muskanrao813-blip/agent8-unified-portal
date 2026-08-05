"""Mock transcription provider for testing without FFmpeg."""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class MockTranscriptionProvider:
    """Mock provider for testing when FFmpeg is not available."""

    def transcribe(self, audio_path: str) -> List[Dict]:
        """Return mock transcription for testing."""
        logger.info(f"[MOCK] Transcribing {audio_path} (mock provider - no FFmpeg needed)")

        # Mock conversation between dietician and patient
        mock_segments = [
            {"speaker": "speaker_0", "text": "Good morning, how are you doing today?", "start_s": 0, "end_s": 3},
            {"speaker": "speaker_1", "text": "I'm doing well, thank you for asking.", "start_s": 4, "end_s": 6},
            {"speaker": "speaker_0", "text": "Let me check your medical history. Do you have any allergies?", "start_s": 7, "end_s": 11},
            {"speaker": "speaker_1", "text": "No, I don't have any allergies.", "start_s": 12, "end_s": 14},
            {"speaker": "speaker_0", "text": "Great! Let's discuss your current diet and lifestyle habits.", "start_s": 15, "end_s": 19},
            {"speaker": "speaker_1", "text": "I try to eat healthy but sometimes I skip meals due to work.", "start_s": 20, "end_s": 25},
            {"speaker": "speaker_0", "text": "That's important to address. Skipping meals can affect your health.", "start_s": 26, "end_s": 31},
            {"speaker": "speaker_0", "text": "I recommend eating 3 balanced meals per day with adequate protein.", "start_s": 32, "end_s": 37},
            {"speaker": "speaker_0", "text": "Let me create a nutrition plan for you. Your goal should be to maintain a healthy BMI.", "start_s": 38, "end_s": 45},
            {"speaker": "speaker_1", "text": "That sounds good. How often should I follow up?", "start_s": 46, "end_s": 49},
            {"speaker": "speaker_0", "text": "Let's schedule a follow-up in 2 weeks to review your progress.", "start_s": 50, "end_s": 55},
        ]

        logger.info(f"[MOCK] Generated {len(mock_segments)} mock segments")
        return mock_segments
