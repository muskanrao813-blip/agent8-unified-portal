"""Clinical-focused LLM analyzer using Claude CLI with improved prompts."""

import json
import logging
import subprocess
import tempfile
import os
from typing import Dict, List
from app.services.llm.base import LLMProvider
from app.services.llm.clinical_prompt import create_clinical_analysis_prompt

logger = logging.getLogger(__name__)


class ClinicalAnalyzer(LLMProvider):
    """Uses Claude CLI for clinical-specific call analysis."""

    def analyze_all_dimensions(
        self,
        transcript_segments: List[Dict],
        metrics: Dict,
        call_id: str,
        dietician_name: str,
        patient_id: str,
        patient_condition: str = "Diabetes"
    ) -> Dict:
        """Analyze using Claude CLI with clinical prompts."""
        try:
            logger.info(f"[Clinical] Analyzing call {call_id} for {patient_condition}...")

            # Format transcript
            transcript_text = self._format_transcript(transcript_segments)

            # Pull Gemini entities from segments if available (enriches Claude's context)
            gemini_entities = {}
            for seg in transcript_segments:
                if seg.get("gemini_entities"):
                    gemini_entities = seg["gemini_entities"]
                    break

            # Inject Gemini entities into metrics so prompt can use them
            if gemini_entities:
                metrics = {**metrics, "gemini_entities": gemini_entities}

            # Create clinical analysis prompt
            prompt = create_clinical_analysis_prompt(transcript_text, metrics, patient_condition)

            # Call Claude CLI
            result = self._call_claude_cli(prompt)

            logger.info(f"[Clinical] Analysis complete for {call_id}")

            # Transform Claude response to match our schema
            return self._transform_to_schema(result)

        except Exception as e:
            logger.error(f"[Clinical] Error: {e}")
            raise

    def _format_transcript(self, segments: List[Dict]) -> str:
        """Format segments into readable transcript for Claude analysis.

        Handles both:
        - Gemini output: segments with speaker='dietician'|'patient'|'unknown'
        - Legacy output: single combined segment with full text
        """
        lines = []

        for seg in segments:
            speaker_raw = seg.get("speaker", "unknown")
            text = seg.get("text", "").strip()
            timestamp = seg.get("start_s", 0)

            if not text:
                continue

            # Map speaker keys to display labels
            if speaker_raw in ("dietician", "agent"):
                label = "Dietician"
            elif speaker_raw in ("patient", "customer"):
                label = "Customer"
            elif speaker_raw == "combined":
                # Full Gemini transcript in one segment — already has [Dietician]/[Customer] labels
                # Return as-is (it's already well-formatted)
                return text
            else:
                label = "Speaker"

            lines.append(f"[{timestamp:.0f}s] {label}: {text}")

        return "\n".join(lines)

    def _call_claude_cli(self, prompt: str) -> Dict:
        """Call Claude CLI using stdin to pass the prompt."""
        try:
            import pathlib
            import re

            claude_npm = pathlib.Path.home() / "AppData" / "Roaming" / "npm" / "claude.cmd"
            claude_cmd = str(claude_npm) if claude_npm.exists() else "claude"

            logger.info("[Clinical] Calling Claude CLI with clinical prompt")

            # Use stdin to pass the prompt (more reliable than command-line args)
            cmd = [claude_cmd, "-p"]

            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300
            )

            output = (result.stdout or "").strip()
            if not output and result.stderr:
                # Claude CLI may output to stderr
                output = result.stderr.strip()

            if not output:
                raise RuntimeError("Claude CLI returned empty output")

            logger.info(f"[Clinical] Got response ({len(output)} chars)")

            # Try to parse JSON from the response
            try:
                # First, try direct JSON parse
                parsed = json.loads(output)
                logger.info("[Clinical] Parsed response as JSON directly")
                return parsed
            except json.JSONDecodeError:
                pass

            # Try to extract JSON from markdown code blocks or embedded in text
            json_patterns = [
                r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
                r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
                r'\{[\s\S]*?"scores"[\s\S]*\}',  # JSON with "scores" key
                r'\{[\s\S]*?\}',                  # Any JSON object
            ]

            for pattern in json_patterns:
                match = re.search(pattern, output)
                if match:
                    json_str = match.group(1) if '```' in pattern else match.group(0)
                    try:
                        parsed = json.loads(json_str)
                        logger.info(f"[Clinical] Extracted JSON using pattern: {pattern[:30]}...")
                        return parsed
                    except json.JSONDecodeError:
                        continue

            # If no JSON found, raise error with sample of output
            output_sample = output[:300] if len(output) > 300 else output
            raise ValueError(f"No JSON found in Claude response. Sample: {output_sample}")

        except json.JSONDecodeError as e:
            logger.error(f"[Clinical] JSON parse error: {e}")
            raise
        except subprocess.TimeoutExpired:
            logger.error("[Clinical] Timeout after 5 minutes")
            raise
        except Exception as e:
            logger.error(f"[Clinical] Error: {e}")
            raise

    def _transform_to_schema(self, claude_response: Dict) -> Dict:
        """Transform Claude response to match FE schema."""
        scores = claude_response.get("scores", {})
        sop = claude_response.get("sop_compliance", {})
        alerts = claude_response.get("qa_alerts", [])
        insights = claude_response.get("insights", {})

        # Calculate overall compliance score
        compliance_score = sop.get("compliance_score", 0)
        sop_compliant = sop.get("compliant", True)

        # Use Claude's qa_alerts directly — deduplicated by title
        # Do NOT also add violation-based alerts separately (that creates duplicates
        # since Claude's qa_alerts already contain all SOP violations)
        seen_titles = set()
        qa_alerts = []
        for alert in alerts:
            title = (alert.get("title") or "").strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            qa_alerts.append({
                "title": title,
                "description": alert.get("description", ""),
                "severity": alert.get("severity", "info"),
                "status": "active",
            })

        return {
            "dimension_scores": {
                "greeting": {
                    "score": scores.get("greeting", 0),
                    "evidence": [],
                    "sub_criteria_met": {}
                },
                "empathy": {
                    "score": scores.get("empathy", 0),
                    "evidence": [],
                    "sub_criteria_met": {}
                },
                "compliance": {
                    "score": scores.get("compliance", 0),
                    "evidence": [],
                    "sub_criteria_met": sop.get("violations", [])
                },
                "technical": {
                    "score": scores.get("technical", 0),
                    "evidence": [],
                    "sub_criteria_met": {}
                }
            },
            "scores": scores,  # Include raw scores for convenience
            "sop_compliance": {
                "compliant": sop_compliant,
                "score": compliance_score,
                "violations": sop.get("violations", [])
            },
            "qa_alerts": qa_alerts,
            "transcript_tags": claude_response.get("transcript_tags", {}),
            "insights": {
                "whatWentWell": insights.get("whatWentWell", []),
                "areasForImprovement": insights.get("areasForImprovement", []),
                "summary": insights.get("summary", ""),
                "trainingGaps": insights.get("trainingGapRecs", [])
            },
            "feedback_summary": insights.get("areasForImprovement", [])
        }
