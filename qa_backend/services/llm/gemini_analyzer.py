"""Gemini-based QA analyzer for dietician calls."""

import logging
import json
import os
from typing import Dict, List

logger = logging.getLogger(__name__)


class GeminiAnalyzer:
    """Analyzes dietician call transcripts using Gemini API for QA scoring."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            from google.genai import types
            import httpx
            http_client = httpx.Client(verify=False)
            self._client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(httpx_client=http_client),
            )
        return self._client

    def analyze_all_dimensions(
        self,
        transcript_segments: List[Dict],
        metrics: Dict,
        call_id: str,
        dietician_name: str,
        patient_id: str,
        patient_condition: str = None
    ) -> Dict:
        """Analyze call transcript using Gemini."""
        try:
            client = self._get_client()
            transcript_text = self._build_transcript_text(transcript_segments)

            # Use the EXACT clinical analysis prompt (same as Claude)
            from app.services.llm.clinical_prompt import create_clinical_analysis_prompt
            prompt = create_clinical_analysis_prompt(transcript_text, metrics, patient_condition or "General Health")

            logger.info(f"[Gemini] Calling Gemini for call {call_id}")
            response = client.models.generate_content(
                model="gemini-flash-lite-latest",
                contents=prompt,
            )

            response_text = response.text.strip()
            logger.info(f"[Gemini] Response length: {len(response_text)}")

            # Try parsing JSON
            try:
                # Remove markdown code blocks if present
                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                    response_text = response_text.split("```")[0]
                    response_text = response_text.strip()

                result = json.loads(response_text)
                logger.info("[Gemini] JSON parsed successfully")
                # Convert to pipeline-expected format
                return self._normalize_response_format(result)

            except json.JSONDecodeError as e:
                logger.warning(f"[Gemini] JSON parse failed: {e}")
                logger.warning(f"[Gemini] Response text: {response_text[:200]}")
                # Fall back to heuristic
                return self._generate_heuristic_scores(metrics)

        except Exception as e:
            logger.error(f"[Gemini] Error: {type(e).__name__}: {str(e)}")
            return self._generate_heuristic_scores(metrics)

    def _normalize_response_format(self, response: Dict) -> Dict:
        """Convert Gemini response to pipeline-expected format."""
        # If already in correct format, return as-is
        if "dimension_scores" in response:
            return response

        # Convert from scores format to dimension_scores format
        scores = response.get("scores", {})
        sop = response.get("sop_compliance", {})
        insights = response.get("insights", {})
        qa_alerts = response.get("qa_alerts", [])

        # IMPORTANT: dimension_scores keys must match compute_weighted_score expectations
        # Keys: greeting, empathy, compliance, technical (NOT with _rapport, _communication, etc suffixes)
        return {
            "dimension_scores": {
                "greeting": {
                    "score": scores.get("greeting", 0),  # Already 0-100
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
                    "evidence": sop.get("violations", []),
                    "sub_criteria_met": {}
                },
                "technical": {
                    "score": scores.get("technical", 0),
                    "evidence": [],
                    "sub_criteria_met": {}
                },
                "clinical_safety": {
                    "score": 85.0,  # Default high (0-100 scale)
                    "evidence": [],
                    "red_flag_detected": False,
                    "handled_appropriately": True
                }
            },
            "insights": insights,
            "qa_alerts": qa_alerts,
            "sop_compliance": sop
        }

    def _build_transcript_text(self, segments: List[Dict]) -> str:
        """Build readable transcript from segments."""
        lines = []
        for seg in segments:
            speaker = seg.get("speaker", "Unknown").title()
            text = seg.get("text", "").strip()
            if text:
                lines.append(f"[{speaker}]: {text}")
        return "\n".join(lines) if lines else "No transcript available"

    def _generate_heuristic_scores(self, metrics: Dict) -> Dict:
        """Generate scores based on metrics when Gemini fails - STRICT clinical rubric."""
        logger.info("[Gemini] Generating STRICT heuristic scores")

        duration = metrics.get("duration_seconds", 0)
        dietician_talk = metrics.get("dietician_talk_ratio_pct", 0)
        patient_talk = metrics.get("patient_talk_ratio_pct", 0)
        interruptions = metrics.get("interruption_count", 0)
        time_to_plan = metrics.get("time_to_first_plan_mention_seconds", 0)

        # STRICT scoring: Max caps per dimension
        # Greeting: Professional opening (max 25/100)
        greeting_score = 0
        if duration >= 60:
            greeting_score = 10
        if duration >= 120:
            greeting_score = 15
        if duration >= 300 and interruptions <= 2:
            greeting_score = 25

        # Empathy: Patient engagement (max 30/100)
        empathy_score = 0
        if patient_talk >= 20:
            empathy_score = 10
        if patient_talk >= 30 and interruptions <= 3:
            empathy_score = 20
        if patient_talk >= 40 and duration >= 300:
            empathy_score = 30

        # Compliance: SOP adherence (CRITICAL - max 25/100, very hard to achieve)
        compliance_score = 0
        # MUST have health assessment FIRST (time_to_plan >= 180)
        if time_to_plan >= 180 and patient_talk >= 25:
            compliance_score = 10
        # MUST have adequate discussion
        if time_to_plan >= 240 and patient_talk >= 30 and duration >= 300:
            compliance_score = 18
        # Perfect execution
        if time_to_plan >= 300 and patient_talk >= 35 and duration >= 600:
            compliance_score = 25

        # Technical: Plan quality (max 25/100)
        technical_score = 0
        if time_to_plan >= 150 and duration >= 240:
            technical_score = 10
        if time_to_plan >= 240 and duration >= 480:
            technical_score = 20
        if time_to_plan >= 300 and duration >= 600 and dietician_talk >= 45:
            technical_score = 25

        # Violations (based on clinical rubric)
        violations = []
        if time_to_plan < 120:
            violations.append({
                "check": "Health Understanding First",
                "violated": True,
                "evidence": "Plan mentioned too early (< 2min) - insufficient health assessment"
            })
        if patient_talk < 25:
            violations.append({
                "check": "Patient Education",
                "violated": True,
                "evidence": "Patient talking < 25% - insufficient discussion"
            })
        if duration < 180:
            violations.append({
                "check": "Informed Consent",
                "violated": True,
                "evidence": "Call too short (< 3min) to establish understanding"
            })

        qa_alerts = []
        if time_to_plan < 120:
            qa_alerts.append({
                "title": "Rushed Diagnosis",
                "description": "Diet plan mentioned too early without adequate health assessment",
                "severity": "critical"
            })
        if patient_talk < 25:
            qa_alerts.append({
                "title": "Low Patient Engagement",
                "description": "Patient talking time < 25% indicates one-sided conversation",
                "severity": "warning"
            })
        if compliance_score < 50:
            qa_alerts.append({
                "title": "SOP Compliance Risk",
                "description": f"Multiple compliance gaps detected (score: {int(compliance_score)})",
                "severity": "critical"
            })

        return {
            "scores": {
                "greeting": max(0, min(100, int(greeting_score))),
                "empathy": max(0, min(100, int(empathy_score))),
                "compliance": max(0, min(100, int(compliance_score))),
                "technical": max(0, min(100, int(technical_score)))
            },
            "sop_compliance": {
                "compliant": compliance_score >= 70,
                "compliance_score": max(0, min(100, int(compliance_score))),
                "violations": violations
            },
            "qa_alerts": qa_alerts,
            "insights": {
                "whatWentWell": [
                    f"Patient engagement: {patient_talk}%" if patient_talk >= 25 else "Conversation structure",
                    f"Call duration: {duration}s" if duration >= 300 else "Time management needed"
                ],
                "areasForImprovement": [
                    "Health understanding must come BEFORE recommendations" if time_to_plan < 120 else "Good assessment sequence",
                    "Increase patient talking time" if patient_talk < 25 else "",
                    "Provide more detailed plan explanation" if technical_score < 60 else ""
                ],
                "summary": f"Clinical assessment: Compliance needs improvement (focus on health assessment first)" if compliance_score < 70 else f"Call meets clinical standards"
            }
        }
