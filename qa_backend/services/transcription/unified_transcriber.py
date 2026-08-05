"""Unified transcription pipeline: faster-whisper + Wav2Vec2 + Claude cleanup."""

import logging
from typing import List, Dict, Optional
from app.services.transcription.base import Segment
from app.services.llm.transcript_cleaner import TranscriptCleaner

logger = logging.getLogger(__name__)

class UnifiedTranscriber:
    """
    Multi-stage transcription pipeline:
    1. Try faster-whisper (fast, general-purpose)
    2. Fallback to Wav2Vec2 (specialized for Hindi/Hinglish)
    3. Clean with Claude CLI (fix errors, remove gibberish)
    """

    @staticmethod
    def transcribe_and_cleanup(audio_path: str) -> tuple[List[Segment], Dict]:
        """
        Transcribe audio using best available backend + Claude cleanup.
        Returns: (segments, metadata)
        """
        logger.info(f"[UnifiedTranscriber] Starting pipeline for {audio_path}")

        segments = []
        metadata = {'steps': []}

        # Step 1: Try faster-whisper
        try:
            logger.info("[UnifiedTranscriber] Step 1: faster-whisper")
            from app.services.transcription.faster_whisper_provider import FasterWhisperProvider

            fw_provider = FasterWhisperProvider()
            segments = fw_provider.transcribe(audio_path)

            metadata['steps'].append({'step': 'faster-whisper', 'status': 'success', 'segments': len(segments)})
            metadata['provider'] = 'faster-whisper'

        except Exception as e:
            logger.warning(f"[UnifiedTranscriber] faster-whisper failed: {e}")
            metadata['steps'].append({'step': 'faster-whisper', 'status': 'failed', 'error': str(e)[:100]})

            # Step 2: Fallback to Wav2Vec2
            try:
                logger.info("[UnifiedTranscriber] Step 2: Wav2Vec2 (Hindi)")
                from app.services.transcription.wav2vec2_provider import Wav2Vec2Provider

                wav2vec_provider = Wav2Vec2Provider()
                segments = wav2vec_provider.transcribe(audio_path)

                metadata['steps'].append({'step': 'wav2vec2', 'status': 'success', 'segments': len(segments)})
                metadata['provider'] = 'wav2vec2'

            except Exception as e2:
                logger.error(f"[UnifiedTranscriber] Wav2Vec2 failed: {e2}")
                metadata['steps'].append({'step': 'wav2vec2', 'status': 'failed', 'error': str(e2)[:100]})
                raise RuntimeError(f"All transcription backends failed. faster-whisper: {e}, Wav2Vec2: {e2}")

        # Step 3: Claude cleanup
        try:
            logger.info("[UnifiedTranscriber] Step 3: Claude cleanup")

            if segments:
                # Combine all segments into one text
                raw_text = '\n'.join([seg.get('text', '') for seg in segments])

                # Clean with Claude
                cleaner = TranscriptCleaner()
                cleanup_result = cleaner.clean_transcript(raw_text)

                if cleanup_result.get('cleaned'):
                    # Update segments with cleaned text
                    for seg in segments:
                        seg['text_cleaned'] = cleanup_result['cleaned']
                        seg['cleanup_confidence'] = cleanup_result.get('confidence', 'unknown')

                metadata['steps'].append({
                    'step': 'claude-cleanup',
                    'status': 'success',
                    'confidence': cleanup_result.get('confidence')
                })
            else:
                logger.warning("[UnifiedTranscriber] No segments to clean")
                metadata['steps'].append({'step': 'claude-cleanup', 'status': 'skipped'})

        except Exception as e:
            logger.warning(f"[UnifiedTranscriber] Claude cleanup failed: {e}")
            metadata['steps'].append({'step': 'claude-cleanup', 'status': 'failed', 'error': str(e)[:100]})
            # Don't fail the entire pipeline if cleanup fails

        logger.info(f"[UnifiedTranscriber] Pipeline complete: {len(segments)} segments")
        return segments, metadata
