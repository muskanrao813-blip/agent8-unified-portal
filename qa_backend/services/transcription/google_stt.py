"""Google Cloud Speech-to-Text implementation with Hinglish support."""

import os
import logging
from typing import List, Dict
from app.services.transcription.base import TranscriptionProvider, Segment

logger = logging.getLogger(__name__)

# Lazy imports to handle Python 3.14 compatibility issues
_speech_client_cache = None
_storage_client_cache = None
_import_error = None

def _get_speech_client():
    """Lazy load speech client to avoid import errors at startup."""
    global _speech_client_cache, _import_error
    if _speech_client_cache is not None:
        return _speech_client_cache
    if _import_error is not None:
        raise _import_error

    try:
        from google.cloud import speech_v1
        _speech_client_cache = speech_v1.SpeechClient()
        return _speech_client_cache
    except Exception as e:
        _import_error = e
        raise

def _get_storage_client():
    """Lazy load storage client to avoid import errors at startup."""
    global _storage_client_cache, _import_error
    if _storage_client_cache is not None:
        return _storage_client_cache
    if _import_error is not None:
        raise _import_error

    try:
        from google.cloud import storage
        _storage_client_cache = storage.Client()
        return _storage_client_cache
    except Exception as e:
        _import_error = e
        raise


class GoogleSTTProvider(TranscriptionProvider):
    def __init__(self, gcs_bucket: str = None, credentials_path: str = None):
        self.gcs_bucket = gcs_bucket or os.getenv("GCS_BUCKET_NAME", "dietician-qa-audio")
        self.credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.raw_response = None
        self._speech_client = None
        self._storage_client = None

    @property
    def speech_client(self):
        """Lazy load speech client."""
        if self._speech_client is None:
            self._speech_client = _get_speech_client()
        return self._speech_client

    @property
    def storage_client(self):
        """Lazy load storage client."""
        if self._storage_client is None:
            self._storage_client = _get_storage_client()
        return self._storage_client

    def transcribe(self, audio_path: str) -> List[Segment]:
        """Transcribe audio with speaker diarization (Hinglish support)."""
        try:
            # Upload to GCS if local file
            gcs_uri = self._upload_to_gcs(audio_path) if audio_path.startswith("/") else audio_path

            # Prepare recognition config with telephony model (optimized for low-quality phone audio)
            config = speech_v1.RecognitionConfig(
                encoding=speech_v1.RecognitionConfig.AudioEncoding.AUTO,
                language_codes=["hi-IN", "en-IN"],  # Hinglish support
                max_alternatives=1,
                diarization_config=speech_v1.SpeakerDiarizationConfig(
                    enable_speaker_diarization=True,
                    min_speaker_count=2,
                    max_speaker_count=2,
                ),
                model="phone_call",  # Telephony model for 8kHz/low-quality audio
                use_enhanced=True,
                enable_automatic_punctuation=True,
            )

            audio = speech_v1.RecognitionAudio(uri=gcs_uri)

            # Use long-running recognize for longer audio
            operation = self.speech_client.long_running_recognize(config=config, audio=audio)
            logger.info(f"Waiting for transcription operation: {operation.name}")

            result = operation.result(timeout=3600)  # Wait up to 1 hour
            self.raw_response = result

            # Extract segments from results
            segments = self._extract_segments(result)
            return segments

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise

    def _upload_to_gcs(self, local_path: str) -> str:
        """Upload local audio file to GCS and return URI."""
        try:
            bucket = self.storage_client.bucket(self.gcs_bucket)
            blob_name = os.path.basename(local_path)
            blob = bucket.blob(blob_name)

            logger.info(f"Uploading {local_path} to gs://{self.gcs_bucket}/{blob_name}")
            blob.upload_from_filename(local_path)

            return f"gs://{self.gcs_bucket}/{blob_name}"
        except Exception as e:
            logger.error(f"Error uploading to GCS: {e}")
            raise

    def _extract_segments(self, result) -> List[Segment]:
        """Extract diarized segments from Google STT response."""
        segments = []

        for result_item in result.results:
            if not result_item.alternatives:
                continue

            alternative = result_item.alternatives[0]

            # Check if we have speaker diarization
            if hasattr(alternative, "words") and alternative.words:
                current_speaker = None
                current_text = []
                current_start = None

                for word_info in alternative.words:
                    speaker_tag = word_info.speaker_tag if hasattr(word_info, "speaker_tag") else None
                    word = word_info.word

                    if speaker_tag != current_speaker and current_text:
                        # End current segment and start new one
                        segment = Segment(
                            speaker=f"speaker_{current_speaker}" if current_speaker else "unknown",
                            text=" ".join(current_text),
                            start_s=round(current_start, 2) if current_start else 0,
                            end_s=round(word_info.start_time.seconds + word_info.start_time.nanos / 1e9, 2),
                        )
                        segments.append(segment)
                        current_text = []
                        current_start = None

                    current_speaker = speaker_tag
                    current_text.append(word)

                    if current_start is None:
                        current_start = word_info.start_time.seconds + word_info.start_time.nanos / 1e9

                # Add final segment
                if current_text:
                    segment = Segment(
                        speaker=f"speaker_{current_speaker}" if current_speaker else "unknown",
                        text=" ".join(current_text),
                        start_s=round(current_start, 2),
                        end_s=round(word_info.end_time.seconds + word_info.end_time.nanos / 1e9, 2),
                    )
                    segments.append(segment)
            else:
                # Fallback if no word-level diarization
                segment = Segment(
                    speaker="unknown",
                    text=alternative.transcript,
                    start_s=0,
                    end_s=0,
                )
                segments.append(segment)

        return segments

    def get_raw_response(self) -> Dict:
        """Return raw API response for audit."""
        if self.raw_response:
            return {"results": [r.to_dict() for r in self.raw_response.results]}
        return {}
