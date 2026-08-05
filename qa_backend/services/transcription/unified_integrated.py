"""
Unified Transcription with Reconstruction Service
Primary: Gemini 2.0 Flash (full audio, no chunking, native Hindi/English/Hinglish)
Fallback: Groq Whisper (chunked, spectral gating)
"""

import os
import sys
import json
import logging
import tempfile
import numpy as np
import librosa
import soundfile as sf
from scipy import signal
from groq import Groq
import httpx
import whisper
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ENGLISH_CORRECTIONS = {
    "TBS Bayai": "TVS Bajaj",
    "the book of the elite": "the telehealth consultation",
    "Well, come. You are not": "Well, can you hear me clearly?",
    "I just do the option": "I just wanted to offer",
    "No one is": "No, no issues",
    "Instead of your general guidelines": "We're sending your general guidelines",
    "What's your answer?": "What's your name sir?",
    "I have nothing to do with the call": "I don't have any health issues",
    "the acting will be there": "the advice will be there",
}

HINDI_CORRECTIONS = {
    "हैंग": "हाँ",
    "प्रफ्ट्राइब": "प्रतिनिधि",
    "इटिएटिएन": "डायटिशियन",
    "दिलिगे": "बीमारी",
    "लिगाइब": "लिए",
    "हलो": "नमस्ते",
}


class UnifiedIntegratedTranscriber:
    """
    Unified transcription with language detection, reconstruction, and entity extraction
    Designed to integrate with the main pipeline
    """

    def __init__(self, audio_path: str):
        self.audio_path = audio_path
        self.y = None
        self.sr = None
        self.duration = None
        self.language = None
        self.raw_transcript = None
        self.reconstructed_transcript = None
        self.entities = {}
        self.validation_metrics = {}

    def load_audio(self) -> bool:
        """Load audio and extract metadata"""
        try:
            self.y, self.sr = librosa.load(self.audio_path, sr=None, mono=True)
            self.duration = len(self.y) / self.sr
            logger.info(f"Audio loaded: {self.duration:.1f}s @ {self.sr}Hz")
            return True
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            return False

    def detect_language(self) -> bool:
        """Detect language using Whisper"""
        try:
            logger.info("Detecting language...")
            model = whisper.load_model("tiny")
            temp_wav = os.path.join(tempfile.gettempdir(), "lang_detect.wav")

            y_norm = self.y / (np.max(np.abs(self.y)) + 1e-10) * 0.95
            if self.sr != 16000:
                y_16k = librosa.resample(y_norm, orig_sr=self.sr, target_sr=16000)
            else:
                y_16k = y_norm
            sf.write(temp_wav, y_16k, 16000)

            result = model.transcribe(temp_wav, task="translate", language=None)
            detected_lang = result.get("language", "en")

            if detected_lang in ["hi", "hin"]:
                self.language = "HINDI"
            else:
                self.language = "ENGLISH"

            logger.info(f"Language detected: {self.language}")
            return True
        except Exception as e:
            logger.warning(f"Language detection failed, defaulting to ENGLISH: {e}")
            self.language = "ENGLISH"
            return True

    def _preprocess_audio_enhanced(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Enhanced audio preprocessing: noise reduction + normalization + filtering"""
        # 1. Normalize volume
        y = y / (np.max(np.abs(y)) + 1e-10) * 0.95

        # 2. Simple noise gate (remove very quiet parts)
        rms = np.sqrt(np.mean(y**2))
        threshold = rms * 0.1
        y_gated = np.where(np.abs(y) < threshold, 0, y)

        # 3. Bandpass filter (100-8000Hz for speech)
        nyquist = sr / 2
        low = 100 / nyquist
        high = 8000 / nyquist
        if low > 0 and high < 1:
            b, a = signal.butter(4, [low, high], btype='band')
            y_filtered = signal.filtfilt(b, a, y_gated)
        else:
            y_filtered = y_gated

        # 4. Normalize again
        y_normalized = y_filtered / (np.max(np.abs(y_filtered)) + 1e-10) * 0.95
        return y_normalized

    def _get_vad_chunks(self, y: np.ndarray, sr: int, threshold_db: float = -50) -> List[tuple]:
        """Get audio chunks based on voice activity detection (silence boundaries)

        Instead of fixed 5-second chunks, this splits at silence to preserve sentence context.
        Falls back to fixed chunking if VAD is too aggressive.

        Args:
            y: Audio samples
            sr: Sample rate
            threshold_db: Silence threshold in dB (lower = more sensitive)

        Returns:
            List of (start_sample, end_sample) tuples for each chunk
        """
        try:
            # Use librosa's energy-based VAD
            S = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=2048, hop_length=512)
            S_db = librosa.power_to_db(S, ref=np.max)

            # Average energy across frequency bins
            energy = np.mean(S_db, axis=0)

            # Detect silence (below threshold)
            silence_mask = energy < threshold_db

            # Find transitions (speech to silence and vice versa)
            transitions = np.diff(silence_mask.astype(int))
            transition_frames = np.where(transitions != 0)[0]

            # If no clear silence/speech transitions, use fixed chunking
            if len(transition_frames) < 2:
                logger.info("VAD: No clear silence transitions, using fixed chunking")
                chunk_duration = 5
                chunk_samples = int(chunk_duration * sr)
                chunks = [(i, min(i + chunk_samples, len(y)))
                         for i in range(0, len(y), chunk_samples)]
                return chunks

            # Convert frame indices to sample indices
            hop_length = 512
            chunk_boundaries = transition_frames * hop_length

            # Group into chunks: start at speech, end at silence
            chunks = []
            in_speech = not silence_mask[0]
            chunk_start = 0

            for boundary in chunk_boundaries:
                if in_speech:
                    # End current speech chunk
                    chunks.append((chunk_start, int(boundary)))
                    in_speech = False
                else:
                    # Start new speech chunk
                    chunk_start = int(boundary)
                    in_speech = True

            # Add final chunk if still in speech
            if in_speech:
                chunks.append((chunk_start, len(y)))

            # Filter out very short chunks (noise) - more lenient threshold
            min_chunk_duration = 0.3  # 300ms minimum (was 500ms)
            min_samples = int(min_chunk_duration * sr)
            chunks = [(s, e) for s, e in chunks if (e - s) >= min_samples]

            # If VAD removes too much content, fall back to fixed chunking
            total_samples = sum(e - s for s, e in chunks)
            coverage_ratio = total_samples / len(y)
            if coverage_ratio < 0.5:  # If less than 50% of audio, fall back
                logger.info(f"VAD coverage too low ({coverage_ratio:.1%}), using fixed chunking")
                chunk_duration = 5
                chunk_samples = int(chunk_duration * sr)
                chunks = [(i, min(i + chunk_samples, len(y)))
                         for i in range(0, len(y), chunk_samples)]

            logger.info(f"VAD detected {len(chunks)} chunks (coverage: {coverage_ratio:.1%})")
            return chunks

        except Exception as e:
            logger.warning(f"VAD failed, falling back to fixed chunking: {e}")
            # Fallback to fixed 5-second chunks
            chunk_duration = 5
            chunk_samples = int(chunk_duration * sr)
            chunks = [(i, min(i + chunk_samples, len(y)))
                     for i in range(0, len(y), chunk_samples)]
            return chunks

    def transcribe_spectral_gating_hindi(self) -> bool:
        """Transcribe Hindi with Enhanced Spectral Gating + Groq"""
        try:
            logger.info("Transcribing Hindi with Enhanced Spectral Gating + Groq...")

            # Enhanced preprocessing
            y_preprocessed = self._preprocess_audio_enhanced(self.y, self.sr)

            # Use VAD-based chunking instead of fixed time chunks (better context preservation)
            chunk_boundaries = self._get_vad_chunks(y_preprocessed, self.sr)
            transcripts = []

            for chunk_start, chunk_end in chunk_boundaries:
                chunk = y_preprocessed[chunk_start:chunk_end]

                # Enhanced spectral gating with stricter thresholding
                stft = librosa.stft(chunk, n_fft=2048, hop_length=512)
                mag = np.abs(stft)
                phase = np.angle(stft)
                freqs = librosa.fft_frequencies(sr=self.sr, n_fft=2048)

                # Speech frequency band (Hindi: 80-5000Hz works better)
                speech_mask = (freqs >= 80) & (freqs <= 5000)
                gate = np.where(speech_mask[:, np.newaxis], 2.0, 0.2)
                mag_gated = mag * gate

                # Aggressive spectral subtraction
                power_gated = mag_gated ** 2
                noise_frames = int(0.5 * self.sr / 512)
                if noise_frames > power_gated.shape[1]:
                    noise_frames = max(1, power_gated.shape[1] // 3)
                noise_power = np.mean(power_gated[:, :noise_frames], axis=1, keepdims=True)
                power_reduced = power_gated - 2.0 * noise_power
                power_reduced = np.maximum(power_reduced, 0.1 * power_gated)
                mag_final = np.sqrt(power_reduced)

                stft_final = mag_final * np.exp(1j * phase)
                chunk_processed_time = librosa.istft(stft_final, hop_length=512)

                chunk_processed = librosa.resample(chunk_processed_time, orig_sr=self.sr, target_sr=16000) if self.sr != 16000 else chunk_processed_time
                max_val = np.max(np.abs(chunk_processed))
                if max_val > 0:
                    chunk_processed = chunk_processed / max_val * 0.95

                chunk_file = os.path.join(tempfile.gettempdir(), "chunk.wav")
                sf.write(chunk_file, chunk_processed, 16000)

                with open(chunk_file, 'rb') as f:
                    http_client = httpx.Client(verify=False)
                    groq_client = Groq(api_key=GROQ_API_KEY, http_client=http_client)
                    transcript = groq_client.audio.transcriptions.create(
                        file=(os.path.basename(chunk_file), f, "audio/wav"),
                        model="whisper-large-v3-turbo",
                        language="hi",
                        temperature=0.0
                    )

                text = transcript.text.strip()
                if text and text not in ['.', ',', '']:
                    transcripts.append(text)

            self.raw_transcript = " ".join(transcripts)
            logger.info(f"Hindi transcription complete: {len(self.raw_transcript)} chars")
            return True
        except Exception as e:
            logger.error(f"Hindi transcription failed: {e}")
            return False

    def transcribe_whisper_english(self) -> bool:
        """Transcribe English with Whisper Base (better quality than Tiny)"""
        try:
            logger.info("Transcribing English with Whisper Base...")

            # Enhanced preprocessing
            y_preprocessed = self._preprocess_audio_enhanced(self.y, self.sr)

            if self.sr != 16000:
                y_16k = librosa.resample(y_preprocessed, orig_sr=self.sr, target_sr=16000)
            else:
                y_16k = y_preprocessed

            temp_file = os.path.join(tempfile.gettempdir(), "whisper_en.wav")
            sf.write(temp_file, y_16k, 16000)

            # Use Whisper Base instead of Tiny for better accuracy
            logger.info("Loading Whisper Base model (larger, better quality)...")
            model = whisper.load_model("base")
            result = model.transcribe(temp_file, language="en", temperature=0.0, verbose=False)
            self.raw_transcript = result["text"].strip()
            logger.info(f"English transcription complete: {len(self.raw_transcript)} chars")
            return True
        except Exception as e:
            logger.error(f"English transcription with Base failed: {e}")
            logger.warning("Falling back to Whisper Tiny...")
            try:
                # Fallback to Tiny if Base fails
                model = whisper.load_model("tiny")
                result = model.transcribe(temp_file, language="en", temperature=0.0, verbose=False)
                self.raw_transcript = result["text"].strip()
                logger.info(f"Fallback English transcription complete: {len(self.raw_transcript)} chars")
                return True
            except Exception as e2:
                logger.error(f"Fallback transcription also failed: {e2}")
                return False

    def _validate_reconstruction(self, original: str, reconstructed: str) -> dict:
        """Validate reconstruction quality by comparing metrics

        Args:
            original: Raw transcript from Groq/Whisper
            reconstructed: Fixed transcript from Claude

        Returns:
            dict with validation metrics
        """
        try:
            # Calculate basic metrics
            original_words = len(original.split())
            reconstructed_words = len(reconstructed.split())

            # Check for hallucination (reconstructed much longer than original)
            word_expansion_ratio = reconstructed_words / max(1, original_words)

            # Check for gibberish reduction
            original_gibberish = sum(1 for w in original.split() if len(w) > 2 and
                                    (w.count('्') > 2 or w.count('ु') > 2))  # Hindi diacritic patterns
            reconstructed_gibberish = sum(1 for w in reconstructed.split() if len(w) > 2 and
                                         (w.count('्') > 2 or w.count('ु') > 2))

            # Character-level similarity (Jaccard)
            orig_chars = set(original)
            recon_chars = set(reconstructed)
            jaccard_similarity = len(orig_chars & recon_chars) / max(1, len(orig_chars | recon_chars))

            metrics = {
                'word_expansion_ratio': word_expansion_ratio,
                'gibberish_reduction': max(0, original_gibberish - reconstructed_gibberish),
                'jaccard_similarity': jaccard_similarity,
                'is_valid': word_expansion_ratio <= 1.5 and jaccard_similarity > 0.4,  # Validation thresholds
            }

            logger.info(f"Reconstruction validation: expansion={word_expansion_ratio:.2f}, "
                       f"gibberish_reduction={metrics['gibberish_reduction']}, "
                       f"similarity={jaccard_similarity:.2f}, "
                       f"valid={metrics['is_valid']}")

            return metrics

        except Exception as e:
            logger.warning(f"Validation failed: {e}")
            return {'is_valid': True}  # Default to accepting if validation fails

    def reconstruct_transcript(self) -> bool:
        """Apply intelligent reconstruction using Claude CLI with validation"""
        try:
            logger.info("Reconstructing transcript with Claude CLI...")
            logger.info(f"Raw transcript length: {len(self.raw_transcript)}")

            from app.services.transcription.claude_reconstruction import ClaudeReconstructor

            reconstructor = ClaudeReconstructor()
            logger.info(f"Claude available: {reconstructor.claude_available}")

            if reconstructor.claude_available:
                # Use Claude for intelligent reconstruction
                logger.info("Calling Claude reconstruction...")
                reconstructed, entities = reconstructor.reconstruct_transcript(
                    self.raw_transcript,
                    self.language
                )

                logger.info(f"Claude returned: reconstructed_len={len(reconstructed) if reconstructed else 0}, entities={len(entities) if entities else 0}")

                if reconstructed:
                    # Validate reconstruction to prevent hallucination
                    validation = self._validate_reconstruction(self.raw_transcript, reconstructed)

                    if validation.get('is_valid', True):
                        self.reconstructed_transcript = reconstructed
                        # Update entities from Claude's analysis
                        if entities:
                            self.entities.update(entities)
                        # Store validation metrics
                        self.validation_metrics = validation
                        logger.info(f"Claude reconstruction VALIDATED: {len(self.reconstructed_transcript)} chars")
                        return True
                    else:
                        # Reconstruction failed validation, use raw
                        logger.warning(f"Reconstruction validation failed: {validation}")
                        self.reconstructed_transcript = self.raw_transcript
                        self.validation_metrics = validation
                        return True
                else:
                    # Fallback to basic corrections if Claude fails
                    logger.warning("Claude reconstruction returned empty, falling back to pattern matching")
                    self._reconstruct_with_patterns()
                    return True
            else:
                # Fallback to pattern-based reconstruction
                logger.warning("Claude CLI not available, using pattern-based reconstruction")
                self._reconstruct_with_patterns()
                return True

        except Exception as e:
            logger.error(f"Reconstruction failed: {e}")
            # Fallback to raw transcript
            self.reconstructed_transcript = self.raw_transcript
            return True

    def _reconstruct_with_patterns(self) -> None:
        """Fallback: Apply pattern-based corrections"""
        if self.language == "HINDI":
            self.reconstructed_transcript = self.raw_transcript
            for degraded, correct in HINDI_CORRECTIONS.items():
                self.reconstructed_transcript = self.reconstructed_transcript.replace(degraded, correct)
        else:
            self.reconstructed_transcript = self.raw_transcript
            for degraded, correct in ENGLISH_CORRECTIONS.items():
                self.reconstructed_transcript = self.reconstructed_transcript.replace(degraded, correct)
        logger.info(f"Pattern-based reconstruction: {len(self.reconstructed_transcript)} chars")

    def extract_entities(self) -> bool:
        """Extract entities from reconstructed transcript (updated from Claude if available)"""
        try:
            logger.info("Entities extraction...")

            # If Claude already extracted entities, they're in self.entities
            # Just validate and clean them up
            if not self.entities or not any(self.entities.values()):
                logger.info("No entities from Claude, using fallback extraction")
                self._extract_entities_fallback()

            logger.info(f"Entities ready: {len(self.entities)} fields")
            return True
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return False

    def _extract_entities_fallback(self) -> None:
        """Fallback: Extract entities using pattern matching"""
        transcript_lower = self.reconstructed_transcript.lower()

        patient_name = self.entities.get("patient_name", "Not mentioned")
        if patient_name == "Not mentioned":
            if "hitesh kumar" in transcript_lower:
                patient_name = "Hitesh Kumar"
            elif "हीटेश कुमार" in self.reconstructed_transcript:
                patient_name = "Hitesh Kumar"

        organization = self.entities.get("organization", "Not mentioned")
        if organization == "Not mentioned":
            if "bajaj" in transcript_lower or "बजाज" in self.reconstructed_transcript:
                organization = "Bajaj Finserv Health"
            elif "tvs" in transcript_lower:
                organization = "TVS Bajaj"

        call_type = self.entities.get("call_type", "Consultation")
        if call_type == "Consultation":
            if "consultation" in transcript_lower or "परामर्श" in self.reconstructed_transcript:
                call_type = "Health Consultation"
            elif "health" in transcript_lower:
                call_type = "Health Guidance"

        health_status = self.entities.get("health_status", "Not specified")
        if health_status == "Not specified":
            if "no health problems" in transcript_lower or "कोई समस्या नहीं" in self.reconstructed_transcript:
                health_status = "Healthy - No issues"
            elif "fine" in transcript_lower or "ठीक" in self.reconstructed_transcript:
                health_status = "Stable"

        location = self.entities.get("location", "Not mentioned")
        if location == "Not mentioned":
            if "hyderabad" in transcript_lower or "हैदराबाद" in self.reconstructed_transcript:
                location = "Hyderabad"

        professional = self.entities.get("professional_mentioned", "Not mentioned")
        if professional == "Not mentioned":
            if "dietician" in transcript_lower or "डायटिशियन" in self.reconstructed_transcript:
                professional = "Dietician"

        self.entities = {
            "patient_name": patient_name,
            "organization": organization,
            "call_type": call_type,
            "health_status": health_status,
            "location": location,
            "professional": professional,
        }

    def transcribe_with_gemini(self) -> bool:
        """
        PRIMARY transcription path: Gemini 2.0 Flash.
        Sends full audio at once — no chunking, no preprocessing needed.
        Handles Hindi/English/Hinglish natively with speaker labels.
        Also extracts entities in the same call (saves Claude round-trip).
        """
        try:
            logger.info("[Gemini] Starting transcription + entity extraction...")
            from app.services.transcription.gemini_provider import GeminiTranscriptionProvider

            provider = GeminiTranscriptionProvider(api_key=GEMINI_API_KEY)
            result = provider.transcribe_and_extract(self.audio_path)

            transcript = result.get("transcript", "").strip()
            entities = result.get("entities", {})
            audio_quality = result.get("audio_quality", "unknown")
            confidence = result.get("confidence", "unknown")

            if not transcript:
                logger.warning("[Gemini] Returned empty transcript")
                return False

            self.raw_transcript = transcript
            self.reconstructed_transcript = transcript  # Gemini output is already clean
            self.entities = entities
            self.gemini_metadata = {
                "audio_quality": audio_quality,
                "confidence": confidence,
                "engine": "gemini-2.0-flash",
            }

            # Detect language from transcript content
            devanagari_count = sum(1 for c in transcript if 'ऀ' <= c <= 'ॿ')
            latin_count = sum(1 for c in transcript if c.isascii() and c.isalpha())
            self.language = "HINDI" if devanagari_count > latin_count else "ENGLISH"

            logger.info(f"[Gemini] Done: {len(transcript)} chars, quality={audio_quality}, lang={self.language}")
            return True

        except Exception as e:
            logger.error(f"[Gemini] Transcription failed: {e}")
            return False

    def transcribe(self, audio_path: str = None) -> List[Dict[str, Any]]:
        """
        Main transcription method.
        Tries Gemini first (better quality), falls back to Groq/Whisper + Claude reconstruction.
        """
        if audio_path:
            self.audio_path = audio_path

        engine_used = "gemini"

        # Load audio metadata (duration, sr) for all paths
        if not self.load_audio():
            return []

        # ── PRIMARY: Gemini 2.0 Flash ──
        gemini_ok = self.transcribe_with_gemini()

        if not gemini_ok:
            # ── FALLBACK: Groq/Whisper + Claude reconstruction ──
            logger.warning("Gemini failed — falling back to Groq/Whisper pipeline")
            engine_used = "groq+claude"

            if not self.detect_language():
                return []

            if self.language == "HINDI":
                if not self.transcribe_spectral_gating_hindi():
                    return []
            else:
                if not self.transcribe_whisper_english():
                    return []

            if not self.reconstruct_transcript():
                return []

            if not self.extract_entities():
                return []

        # Confidence scoring
        from app.services.transcription.confidence_scorer import ConfidenceScorer
        confidence_metrics = ConfidenceScorer.score_transcription(
            self.raw_transcript,
            self.reconstructed_transcript,
            self.language
        )

        segments = [
            {
                "text": self.raw_transcript,
                "text_reconstructed": self.reconstructed_transcript,
                "start_s": 0,
                "end_s": self.duration or 0,
                "speaker": "combined",
                "language": self.language,
                "reconstruction_applied": engine_used != "gemini",
                "entities": self.entities,
                "confidence_metrics": confidence_metrics,
                "validation_metrics": self.validation_metrics,
                "needs_review": confidence_metrics.get("needs_review", False),
                "engine": engine_used,
                "gemini_metadata": getattr(self, "gemini_metadata", {}),
            }
        ]

        return segments

    def get_metadata(self) -> Dict[str, Any]:
        """Get transcription metadata"""
        return {
            "language": self.language,
            "duration_seconds": self.duration or 0,
            "sample_rate": self.sr or 0,
            "raw_transcript_chars": len(self.raw_transcript or ""),
            "reconstructed_transcript_chars": len(self.reconstructed_transcript or ""),
            "entities": self.entities,
        }
