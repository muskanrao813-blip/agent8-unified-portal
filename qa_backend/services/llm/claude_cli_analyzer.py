"""Claude CLI-based LLM analyzer (uses installed Claude Code CLI)."""

import json
import logging
import subprocess
import tempfile
import os
import sys
from typing import Dict, List
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class ClaudeCliAnalyzer(LLMProvider):
    """Uses Claude CLI for real LLM analysis."""

    def analyze_all_dimensions(
        self,
        transcript_segments: List[Dict],
        metrics: Dict,
        call_id: str,
        dietician_name: str,
        patient_id: str
    ) -> Dict:
        """Analyze using Claude CLI."""
        try:
            logger.info(f"[Claude CLI] Analyzing call {call_id}...")

            # Format transcript
            transcript_text = self._format_transcript(transcript_segments)

            # Create analysis prompt
            prompt = self._create_prompt(transcript_text, metrics)

            # Call Claude CLI
            result = self._call_claude_cli(prompt)

            logger.info(f"[Claude CLI] Analysis complete for {call_id}")
            return result

        except Exception as e:
            logger.error(f"[Claude CLI] Error: {e}")
            raise

    def _format_transcript(self, segments: List[Dict]) -> str:
        """Format segments into readable transcript."""
        lines = []
        for seg in segments:
            speaker = seg.get("speaker", "Unknown").replace("_", " ").title()
            text = seg.get("text", "")
            timestamp = seg.get("start_s", 0)
            lines.append(f"[{timestamp:.1f}s] {speaker}: {text}")
        return "\n".join(lines)

    def _create_prompt(self, transcript: str, metrics: Dict) -> str:
        """Create the analysis prompt."""
        return f"""Analyze this dietician-patient call transcript against 6 quality dimensions.

TRANSCRIPT:
{transcript}

METRICS:
- Duration: {metrics.get('duration_seconds', 0)}s
- Dietician talk: {metrics.get('dietician_talk_ratio_pct', 0)}%
- Patient talk: {metrics.get('patient_talk_ratio_pct', 0)}%
- Interruptions: {metrics.get('interruption_count', 0)}
- Avg latency: {metrics.get('avg_response_latency_seconds', 0)}s
- Time to plan: {metrics.get('time_to_first_plan_mention_seconds', 'N/A')}s
- Silence: {metrics.get('silence_pct', 0)}%

Analyze and score (0-10) these 6 dimensions based on the transcript:

1. **Discovery & Assessment (20%)**: Did dietician explore medical history, lifestyle, dietary habits, goals, allergies?
2. **Empathy & Communication (20%)**: Warm tone? Good balance? Active listening? Patient engaged?
3. **Rushed/Forced Detection (15%)**: Was plan prescribed too quickly without proper discovery?
4. **Adherence Counselling (20%)**: Motivation explained? Why adherence matters? Practical? Barriers addressed?
5. **Consultation Completeness (25%)**: Goals confirmed? BMI/weight reviewed? Conditions in plan? Follow-up clear?
6. **Clinical Safety (Gate)**: Any red flags mentioned? If yes, handled appropriately?

For each dimension provide:
- score (0-10 number)
- 2-3 evidence quotes from transcript with timestamps
- sub_criteria_met (which specific criteria were met as true/false)

Return ONLY valid JSON (no markdown, no code blocks, pure JSON):
{{
  "dimension_scores": {{
    "discovery_assessment": {{
      "score": <number>,
      "evidence": [{{"quote": "...", "timestamp_s": <number>}}, ...],
      "sub_criteria_met": {{"medical_history": <bool>, "lifestyle_activity": <bool>, "dietary_habits": <bool>, "goal_alignment": <bool>, "allergy_screening": <bool>}}
    }},
    "empathy_communication": {{
      "score": <number>,
      "evidence": [...],
      "sub_criteria_met": {{"empathy_tone": <bool>, "conversation_balance": <bool>, "active_listening": <bool>, "patient_engagement": <bool>, "sentiment": "positive|neutral|negative"}}
    }},
    "rushed_forced_detection": {{
      "score": <number>,
      "evidence": [...],
      "is_forced": <bool>,
      "is_missing_discovery": <bool>
    }},
    "adherence_counselling": {{
      "score": <number>,
      "evidence": [...],
      "sub_criteria_met": {{"motivation": <bool>, "importance_explained": <bool>, "practical_implementation": <bool>, "barriers_addressed": <bool>}}
    }},
    "consultation_completeness": {{
      "score": <number>,
      "evidence": [...],
      "sub_criteria_met": {{"goals_documented": <bool>, "bmi_reviewed": <bool>, "conditions_incorporated": <bool>, "followup_shared": <bool>}}
    }},
    "clinical_safety": {{
      "score": <number>,
      "evidence": [...],
      "red_flag_detected": <bool>,
      "handled_appropriately": <bool|null>
    }}
  }},
  "feedback_summary": ["Feedback point 1", "Feedback point 2", ...]
}}"""

    def _call_claude_cli(self, prompt: str) -> Dict:
        """Call Claude CLI using its non-interactive print mode."""
        try:
            import pathlib

            claude_npm = pathlib.Path.home() / "AppData" / "Roaming" / "npm" / "claude.cmd"
            if claude_npm.exists():
                claude_cmd = str(claude_npm)
                logger.info(f"[Claude CLI] Found at: {claude_npm}")
            else:
                claude_cmd = "claude"
                logger.info("[Claude CLI] Using 'claude' from PATH")

            logger.info("[Claude CLI] Calling Claude with prompt via --print")

            cmd = [
                claude_cmd,
                "-p",
                prompt,
                "--output-format",
                "json",
                "--permission-mode",
                "bypassPermissions",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300
            )

            output = (result.stdout or result.stderr or "").strip()
            if not output:
                logger.error("[Claude CLI] Empty response")
                raise RuntimeError("Claude CLI returned empty output")

            logger.info(f"[Claude CLI] Got response ({len(output)} chars)")

            try:
                parsed = json.loads(output)
            except json.JSONDecodeError:
                import re
                json_pattern = r'\{[\s\S]*"dimension_scores"[\s\S]*\}'
                match = re.search(json_pattern, output)
                if match:
                    parsed = json.loads(match.group(0))
                else:
                    match = re.search(r'\{[\s\S]*\}', output)
                    if match:
                        parsed = json.loads(match.group(0))
                    else:
                        logger.error(f"[Claude CLI] No JSON found in output")
                        logger.error(f"[Claude CLI] Output: {output[:300]}")
                        raise ValueError("No JSON in Claude response")

            if isinstance(parsed, dict) and parsed.get("is_error"):
                detail = parsed.get("result") or parsed.get("message") or output
                raise RuntimeError(f"Claude CLI rejected the request: {detail}")

            if isinstance(parsed, dict) and "result" in parsed and isinstance(parsed["result"], str):
                result_text = parsed["result"].strip()
                if result_text.startswith("{"):
                    return json.loads(result_text)
                if result_text:
                    return {"text": result_text}

            if result.returncode != 0:
                logger.error(f"[Claude CLI] Exit code {result.returncode}: {output[:1000]}")
                raise RuntimeError(f"Claude CLI failed with code {result.returncode}: {output[:1000]}")

            logger.info("[Claude CLI] Parsed successfully")
            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"[Claude CLI] JSON parse error: {e}")
            raise
        except subprocess.TimeoutExpired:
            logger.error("[Claude CLI] Timeout after 5 minutes")
            raise
        except Exception as e:
            logger.error(f"[Claude CLI] Error: {type(e).__name__}: {e}")
            raise
