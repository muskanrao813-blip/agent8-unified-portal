"""
Confidence scoring for transcriptions
Calculates WER (Word Error Rate) and CER (Character Error Rate) metrics
"""

import logging
from typing import Dict, Any
import difflib

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Score confidence of transcriptions using multiple metrics"""

    @staticmethod
    def calculate_wer(reference: str, hypothesis: str) -> float:
        """Calculate Word Error Rate

        WER = (S + D + I) / N
        where S = substitutions, D = deletions, I = insertions, N = reference length

        Returns:
            WER as percentage (0-1 range, where 0 = perfect, 1 = completely wrong)
        """
        ref_words = reference.split()
        hyp_words = hypothesis.split()

        if len(ref_words) == 0:
            return 0.0 if len(hyp_words) == 0 else 1.0

        # Use difflib to find edit operations
        matcher = difflib.SequenceMatcher(None, ref_words, hyp_words)
        matches = sum(block.size for block in matcher.get_matching_blocks())

        # Calculate errors
        substitutions = len(ref_words) - matches
        deletions = max(0, len(ref_words) - len(hyp_words))
        insertions = max(0, len(hyp_words) - len(ref_words))

        # More accurate calculation using Levenshtein-like distance
        errors = abs(len(ref_words) - len(hyp_words))
        for i, (r, h) in enumerate(zip(ref_words, hyp_words)):
            if r != h:
                errors += 1

        wer = errors / len(ref_words)
        return min(1.0, wer)  # Cap at 1.0

    @staticmethod
    def calculate_cer(reference: str, hypothesis: str) -> float:
        """Calculate Character Error Rate

        CER = (S + D + I) / N
        where S = substitutions, D = deletions, I = insertions, N = reference length

        Returns:
            CER as percentage (0-1 range)
        """
        if len(reference) == 0:
            return 0.0 if len(hypothesis) == 0 else 1.0

        # Use difflib for character-level matching
        matcher = difflib.SequenceMatcher(None, reference, hypothesis)
        matches = sum(block.size for block in matcher.get_matching_blocks())

        errors = len(reference) - matches + abs(len(reference) - len(hypothesis))
        cer = errors / len(reference)
        return min(1.0, cer)

    @staticmethod
    def calculate_bleu_score(reference: str, hypothesis: str, n_gram: int = 2) -> float:
        """Calculate BLEU-like score for ngram similarity

        Returns:
            Score between 0-1 (1 = perfect match, 0 = no match)
        """
        ref_ngrams = set()
        hyp_ngrams = set()

        # Generate ngrams
        for i in range(len(reference) - n_gram + 1):
            ref_ngrams.add(reference[i:i + n_gram])
        for i in range(len(hypothesis) - n_gram + 1):
            hyp_ngrams.add(hypothesis[i:i + n_gram])

        if not ref_ngrams:
            return 1.0 if not hyp_ngrams else 0.0

        # Calculate Jaccard similarity
        intersection = len(ref_ngrams & hyp_ngrams)
        union = len(ref_ngrams | hyp_ngrams)

        return intersection / union if union > 0 else 0.0

    @staticmethod
    def score_transcription(raw: str, reconstructed: str, language: str = "ENGLISH") -> Dict[str, Any]:
        """Score overall transcription quality and confidence

        NOTE: For speech-to-text reconstruction, we expect raw vs reconstructed to differ
        significantly because Claude is fixing phonetic errors and restructuring for coherence.
        We measure QUALITY of reconstruction, not SIMILARITY to raw.

        Args:
            raw: Raw transcript from STT engine
            reconstructed: Reconstructed transcript from Claude
            language: Language of transcript

        Returns:
            Dictionary with all confidence metrics
        """
        try:
            # For reconstruction tasks, evaluate quality not similarity
            # Check 1: Does reconstructed remove gibberish patterns?
            raw_words = raw.split() if raw else []
            recon_words = reconstructed.split() if reconstructed else []

            if len(raw) == 0 or len(reconstructed) == 0:
                # Handle empty results
                if len(raw) == 0 and len(reconstructed) == 0:
                    confidence = "very_high"
                    confidence_score = 0.95
                    is_reliable = False
                else:
                    confidence = "very_low"
                    confidence_score = 0.25
                    is_reliable = False

                metrics = {
                    "reconstruction_quality": "empty",
                    "raw_length": len(raw),
                    "reconstructed_length": len(reconstructed),
                    "confidence": confidence,
                    "confidence_score": round(confidence_score, 2),
                    "is_reliable": is_reliable,
                    "needs_review": len(reconstructed) == 0,
                }
                return metrics

            # Check 2: Coherence improvement (sentences, punctuation)
            raw_has_punctuation = any(p in raw for p in '.!?।')
            recon_has_punctuation = any(p in reconstructed for p in '.!?।')
            coherence_improved = recon_has_punctuation and not raw_has_punctuation

            # Check 3: Length ratio (shouldn't expand too much)
            length_ratio = len(reconstructed) / max(1, len(raw))
            reasonable_expansion = length_ratio < 2.0 and length_ratio > 0.3

            # Check 4: Word count change (should be similar or improved)
            word_change_ratio = len(recon_words) / max(1, len(raw_words))
            reasonable_word_count = 0.5 < word_change_ratio < 1.5

            # Confidence level based on reconstruction quality
            quality_indicators = sum([
                coherence_improved,
                reasonable_expansion,
                reasonable_word_count,
                len(reconstructed) > 20,  # Minimum content threshold
            ])

            if quality_indicators >= 4:
                confidence = "very_high"
                confidence_score = 0.95
            elif quality_indicators >= 3:
                confidence = "high"
                confidence_score = 0.85
            elif quality_indicators >= 2:
                confidence = "medium"
                confidence_score = 0.70
            elif quality_indicators >= 1:
                confidence = "low"
                confidence_score = 0.50
            else:
                confidence = "very_low"
                confidence_score = 0.25

            is_reliable = quality_indicators >= 2 and reasonable_expansion

            metrics = {
                "reconstruction_quality": "good" if is_reliable else "poor",
                "coherence_improved": coherence_improved,
                "expansion_reasonable": reasonable_expansion,
                "word_count_reasonable": reasonable_word_count,
                "raw_length": len(raw),
                "reconstructed_length": len(reconstructed),
                "raw_words": len(raw_words),
                "reconstructed_words": len(recon_words),
                "confidence": confidence,  # very_high, high, medium, low, very_low
                "confidence_score": round(confidence_score, 2),  # 0-1 numeric
                "is_reliable": is_reliable,
                "needs_review": confidence_score < 0.70,
                "quality_score": round(quality_indicators / 4.0, 2),
            }

            logger.info(f"Reconstruction quality: {metrics['reconstruction_quality']}, "
                       f"confidence={confidence}, reliable={is_reliable}")

            return metrics

        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return {
                "reconstruction_quality": "unknown",
                "confidence": "unknown",
                "confidence_score": 0.5,
                "is_reliable": False,
                "needs_review": True,
                "error": str(e),
            }
