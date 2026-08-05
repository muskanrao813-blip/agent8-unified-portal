"""Audio preprocessing to improve degraded/low-quality recordings."""

import logging
import numpy as np
from scipy import signal
from scipy.fft import fft, ifft
import librosa
import soundfile as sf
import tempfile
import os

logger = logging.getLogger(__name__)

class AudioPreprocessor:
    """Preprocess degraded audio for better STT accuracy."""

    @staticmethod
    def preprocess(audio_path: str, output_path: str = None) -> str:
        """
        Comprehensive preprocessing pipeline:
        1. Load audio
        2. Noise reduction (spectral subtraction)
        3. Upsample to 16kHz if needed
        4. Equalization (boost speech frequencies 300-3400Hz)
        5. Normalization
        6. Remove silence/gaps
        7. Save processed audio

        Returns: path to preprocessed audio file
        """
        try:
            logger.info(f"[AudioPreprocessor] Loading {audio_path}")

            # Step 1: Load audio at native sample rate first
            y, sr = librosa.load(audio_path, sr=None, mono=True)
            logger.info(f"[AudioPreprocessor] Original: {sr}Hz, {len(y)} samples, {len(y)/sr:.2f}s")

            # Step 2: Noise reduction using spectral subtraction
            logger.info("[AudioPreprocessor] Step 1: Noise reduction (spectral subtraction)")
            y = AudioPreprocessor._spectral_subtraction(y, sr)

            # Step 3: Upsample to 16kHz if needed
            if sr != 16000:
                logger.info(f"[AudioPreprocessor] Step 2: Upsampling {sr}Hz -> 16kHz")
                y = librosa.resample(y, orig_sr=sr, target_sr=16000)
                sr = 16000

            # Step 4: Speech-focused equalization (boost 300-3400Hz)
            logger.info("[AudioPreprocessor] Step 3: Speech equalization (300-3400Hz)")
            y = AudioPreprocessor._speech_eq(y, sr)

            # Step 5: Normalize audio levels
            logger.info("[AudioPreprocessor] Step 4: Normalization")
            y = AudioPreprocessor._normalize(y)

            # Step 6: Remove silence
            logger.info("[AudioPreprocessor] Step 5: Silence removal")
            y = AudioPreprocessor._remove_silence(y, sr)

            # Step 7: Final normalization after silence removal
            y = AudioPreprocessor._normalize(y)

            logger.info(f"[AudioPreprocessor] Processed: {sr}Hz, {len(y)} samples")

            # Step 8: Save
            if output_path is None:
                output_path = os.path.join(tempfile.gettempdir(), "audio_preprocessed.wav")

            sf.write(output_path, y, sr)
            logger.info(f"[AudioPreprocessor] Saved: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"[AudioPreprocessor] Error: {type(e).__name__}: {e}")
            raise

    @staticmethod
    def _spectral_subtraction(y: np.ndarray, sr: int, noise_duration: float = 1.0) -> np.ndarray:
        """
        Reduce noise using spectral subtraction.
        Assumes first 1 second is noise (or mostly noise).
        """
        try:
            n_fft = 2048
            hop_length = 512

            # Estimate noise from first second
            noise_sample_count = int(noise_duration * sr)
            noise_sample = y[:noise_sample_count]

            # Compute noise power spectrum
            noise_stft = librosa.stft(noise_sample, n_fft=n_fft, hop_length=hop_length)
            noise_power = np.abs(noise_stft) ** 2
            noise_mean = np.mean(noise_power, axis=1, keepdims=True)

            # Compute STFT of full signal
            stft = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            power = magnitude ** 2

            # Spectral subtraction
            power_reduced = power - 2 * noise_mean  # Aggressive subtraction
            power_reduced = np.maximum(power_reduced, 0.1 * power)  # Floor to prevent over-subtraction
            magnitude_reduced = np.sqrt(power_reduced)

            # Reconstruct
            stft_reduced = magnitude_reduced * np.exp(1j * phase)
            y_reduced = librosa.istft(stft_reduced, hop_length=hop_length)

            logger.info("[AudioPreprocessor] Spectral subtraction complete")
            return y_reduced

        except Exception as e:
            logger.warning(f"[AudioPreprocessor] Spectral subtraction failed: {e}, skipping")
            return y

    @staticmethod
    def _speech_eq(y: np.ndarray, sr: int) -> np.ndarray:
        """
        Apply equalization to boost speech frequencies (300-3400Hz).
        Reduce very low (<100Hz) and very high (>5000Hz) frequencies.
        """
        try:
            # Design highpass filter (remove rumble <100Hz)
            sos_hp = signal.butter(4, 100, 'hp', fs=sr, output='sos')
            y = signal.sosfilt(sos_hp, y)

            # Design bandpass filter (300-3400Hz for speech)
            sos_bp = signal.butter(4, [300, 3400], 'band', fs=sr, output='sos')
            speech_band = signal.sosfilt(sos_bp, y)

            # Blend: 60% speech band + 40% original
            y = 0.6 * speech_band + 0.4 * y

            logger.info("[AudioPreprocessor] Speech EQ complete")
            return y

        except Exception as e:
            logger.warning(f"[AudioPreprocessor] Speech EQ failed: {e}, skipping")
            return y

    @staticmethod
    def _normalize(y: np.ndarray) -> np.ndarray:
        """Normalize audio to -20dB (prevent clipping)."""
        try:
            rms = np.sqrt(np.mean(y ** 2))
            if rms > 0:
                target_rms = 10 ** (-20 / 20)  # -20dB
                y = y * (target_rms / rms)
            return np.clip(y, -0.99, 0.99)
        except Exception as e:
            logger.warning(f"[AudioPreprocessor] Normalization failed: {e}")
            return y

    @staticmethod
    def _remove_silence(y: np.ndarray, sr: int, threshold_db: float = -40) -> np.ndarray:
        """Remove leading/trailing silence and short gaps."""
        try:
            # Compute energy
            S = librosa.feature.melspectrogram(y=y, sr=sr)
            S_db = librosa.power_to_db(S, ref=np.max)
            energy = np.mean(S_db, axis=0)

            # Find non-silent frames
            non_silent = energy > threshold_db

            if np.any(non_silent):
                first_true = np.argmax(non_silent)
                last_true = len(non_silent) - np.argmax(non_silent[::-1])

                # Convert frame indices to sample indices
                hop_length = 512
                start_sample = max(0, first_true * hop_length - sr // 20)  # Add 50ms padding
                end_sample = min(len(y), last_true * hop_length + sr // 20)

                y = y[start_sample:end_sample]
                logger.info(f"[AudioPreprocessor] Removed silence: {start_sample} - {end_sample}")

            return y

        except Exception as e:
            logger.warning(f"[AudioPreprocessor] Silence removal failed: {e}")
            return y
