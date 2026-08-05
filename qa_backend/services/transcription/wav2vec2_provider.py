"""Wav2Vec2 implementation with Hindi/Hinglish support."""

import logging
import os
from typing import List, Dict
from app.services.transcription.base import TranscriptionProvider, Segment

logger = logging.getLogger(__name__)

class Wav2Vec2Provider(TranscriptionProvider):
    """Speech-to-text using Wav2Vec2 with Hindi/Hinglish models."""

    def __init__(self):
        self.raw_response = None
        self.processor = None
        self.model = None

    def transcribe(self, audio_path: str) -> List[Segment]:
        """Transcribe audio using Wav2Vec2 Hindi model."""
        try:
            import torch
            import librosa
            from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
            import ssl
            import urllib3

            logger.info(f"[Wav2Vec2] Transcribing {audio_path}")

            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            # Disable SSL verification for model downloads
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            ssl._create_default_https_context = ssl._create_unverified_context
            os.environ['HF_HUB_DISABLE_SSL'] = 'true'

            # Load Hindi Wav2Vec2 model from Hugging Face
            logger.info("[Wav2Vec2] Loading Hindi model (Harveenchadha/vakyansh-wav2vec2-hindi-him-4200)...")
            model_id = "Harveenchadha/vakyansh-wav2vec2-hindi-him-4200"

            try:
                processor = Wav2Vec2Processor.from_pretrained(model_id)
                model = Wav2Vec2ForCTC.from_pretrained(model_id)
                logger.info("[Wav2Vec2] Model loaded successfully")
            except Exception as e:
                logger.error(f"[Wav2Vec2] Failed to load model: {e}")
                raise

            # Load and resample audio to 16kHz (Wav2Vec2 requires 16kHz)
            logger.info("[Wav2Vec2] Loading and resampling audio to 16kHz...")
            try:
                audio, sr = librosa.load(audio_path, sr=16000)
                logger.info(f"[Wav2Vec2] Audio loaded: {len(audio)} samples at 16kHz")
            except Exception as e:
                logger.error(f"[Wav2Vec2] Failed to load audio: {e}")
                raise

            # Process audio
            logger.info("[Wav2Vec2] Processing audio...")
            input_values = processor(audio, sampling_rate=16000, return_tensors="pt").input_values

            # Inference
            logger.info("[Wav2Vec2] Running inference...")
            with torch.no_grad():
                logits = model(input_values).logits

            # Decode
            logger.info("[Wav2Vec2] Decoding output...")
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = processor.batch_decode(predicted_ids)[0]

            logger.info(f"[Wav2Vec2] Transcription ({len(transcription)} chars): {transcription[:150]}")

            # Return as single segment (Wav2Vec2 doesn't segment)
            audio_duration = len(audio) / sr
            self.raw_response = {
                'segments': [{'text': transcription, 'start': 0, 'end': audio_duration}],
                'language': 'hi',
                'duration': audio_duration,
            }

            segments = [Segment({
                'speaker': 'speaker_0',
                'text': transcription,
                'start_s': 0,
                'end_s': audio_duration,
            })]

            logger.info(f"[Wav2Vec2] Complete - {len(transcription)} chars")
            return segments

        except ImportError as e:
            logger.error(f"[Wav2Vec2] Missing dependency: {e}")
            raise RuntimeError(f"Missing required package: {e}")
        except Exception as e:
            logger.error(f"[Wav2Vec2] Error: {type(e).__name__}: {e}")
            raise

    def get_raw_response(self) -> Dict:
        """Return raw response for audit."""
        return self.raw_response or {}
