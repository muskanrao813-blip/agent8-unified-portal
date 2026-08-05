"""Claude Code Skill-based LLM implementation (uses CLI, no API key needed)."""

import json
import logging
import subprocess
from typing import Dict, List
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class ClaudeSkillProvider(LLMProvider):
    """Uses Claude Code CLI skill for analysis (no API key required!)."""

    def analyze_all_dimensions(
        self,
        transcript_segments: List[Dict],
        metrics: Dict,
        call_id: str,
        dietician_name: str,
        patient_id: str
    ) -> Dict:
        """Analyze using Claude Code skill via CLI."""
        try:
            logger.info(f"Calling Claude Code skill for call {call_id}...")

            # Prepare input data
            input_data = {
                "call_id": call_id,
                "dietician_name": dietician_name,
                "patient_id": patient_id,
                "transcript_segments": transcript_segments,
                "metrics": metrics
            }

            # Call the skill
            result = subprocess.run(
                ["claude", "skill", "dietician-qa-analyzer"],
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                logger.error(f"Skill error: {result.stderr}")
                raise RuntimeError(f"Claude skill failed: {result.stderr}")

            # Parse response
            response = json.loads(result.stdout)
            logger.info(f"Claude skill analysis complete for call {call_id}")

            return response

        except subprocess.TimeoutExpired:
            logger.error(f"Claude skill timed out for call {call_id}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse skill response: {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling Claude skill: {e}")
            raise
