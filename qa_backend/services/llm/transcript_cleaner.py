"""Claude API-based transcription cleanup and correction."""

import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

class TranscriptCleaner:
    """Uses Claude API to fix and enhance transcriptions."""

    @staticmethod
    def clean_transcript(raw_text: str) -> Dict:
        """
        Clean transcription using Claude API:
        - Fix repeated words/gibberish
        - Remove filler words
        - Fix Hinglish code-switching
        - Correct common ASR errors
        """
        try:
            logger.info("[ClaudeClean] Cleaning transcript...")

            prompt = f"""Fix this medical transcription from automatic speech recognition. The transcription may contain errors, repeated words, or gibberish.

RULES:
1. Remove repeated words (e.g., "नहीं नहीं नहीं..." → "नहीं")
2. Remove filler words/sounds (um, uh, hmm, eh, huh)
3. Fix Hinglish code-switching (keep both Hindi and English, just fix word order)
4. Fix common homophones (to/two/too, right/write, there/their)
5. Remove stuttering (e.g., "d-d-did" → "did")
6. Preserve all medical terms and patient information
7. Keep the original meaning exactly
8. Remove complete garbage lines (nonsense English/Hindi that don't make sense)

ORIGINAL TRANSCRIPT:
{raw_text}

OUTPUT FORMAT:
Provide ONLY the corrected text, no explanations."""

            # Try Claude API
            try:
                import anthropic

                client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                cleaned_text = message.content[0].text.strip()
                logger.info(f"[ClaudeClean] Cleaned text length: {len(cleaned_text)}")

                return {
                    'cleaned': cleaned_text,
                    'confidence': 'high',
                    'original_length': len(raw_text),
                    'cleaned_length': len(cleaned_text),
                }
            except Exception as api_e:
                logger.warning(f"[ClaudeClean] Claude API failed: {api_e}")
                # Fallback to regex-based cleanup
                return TranscriptCleaner._regex_cleanup(raw_text)

        except Exception as e:
            logger.error(f"[ClaudeClean] Error: {type(e).__name__}: {e}")
            return {'cleaned': raw_text, 'confidence': 'low', 'error': str(e)[:100]}

    @staticmethod
    def _regex_cleanup(text: str) -> Dict:
        """Fallback regex-based cleanup when Claude API unavailable."""
        import re

        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Skip lines that are pure repetition
            words = line.split()
            if len(words) > 0 and len(set(words)) == 1 and len(words) > 5:
                # Line is same word repeated - skip it
                logger.debug(f"[ClaudeClean] Skipping repeated line: {line[:50]}")
                continue

            # Skip obvious garbage (like "No Omega Magi War")
            if any(x in line for x in ["Omega", "Magi", "War"]):
                logger.debug(f"[ClaudeClean] Skipping garbage line: {line}")
                continue

            cleaned_lines.append(line)

        cleaned_text = '\n'.join(cleaned_lines).strip()

        return {
            'cleaned': cleaned_text,
            'confidence': 'medium',
            'original_length': len(text),
            'cleaned_length': len(cleaned_text),
            'method': 'regex_fallback'
        }

    @staticmethod
    def extract_medical_entities(text: str) -> Dict:
        """
        Extract medical entities using Claude CLI:
        - Medications
        - Conditions/symptoms
        - Dosages
        - Follow-up actions
        """
        try:
            logger.info("[ClaudeExtract] Extracting medical entities...")

            prompt = f"""Extract medical entities from this dietician consultation transcript.

TRANSCRIPT:
{text}

Extract:
1. Patient conditions/symptoms mentioned
2. Dietary recommendations
3. Medications/supplements mentioned
4. Follow-up actions
5. Measurements/values (BP, cholesterol, weight, etc.)

Return as JSON with keys: conditions, dietary_recommendations, medications, followup, measurements"""

            result = subprocess.run(
                ["claude", "-p"],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode != 0:
                logger.warning(f"[ClaudeExtract] Failed: {result.stderr[:100]}")
                return {}

            # Try to extract JSON from response
            try:
                # Look for JSON block
                json_match = re.search(r'\{[^{}]*\}', result.stdout, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass

            return {'raw': result.stdout}

        except Exception as e:
            logger.error(f"[ClaudeExtract] Error: {e}")
            return {}
