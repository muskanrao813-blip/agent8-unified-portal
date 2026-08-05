"""Claude API implementation for rubric analysis."""

import json
import logging
import os
from typing import Dict, List
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class ClaudeAPIProvider(LLMProvider):
    """Claude API-based rubric analysis (works with Python 3.14)."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self._client = None

    @property
    def client(self):
        """Lazy load Anthropic client."""
        if self._client is None:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def analyze_all_dimensions(
        self,
        transcript_segments: List[Dict],
        metrics: Dict,
        call_id: str,
        dietician_name: str,
        patient_id: str
    ) -> Dict:
        """Analyze all dimensions with Claude API."""
        try:
            # Format transcript
            transcript_text = self._format_transcript(transcript_segments)

            # Format system prompt
            system_prompt = """You are an expert healthcare quality analyst specializing in evaluating dietician consultation transcripts.

Your task is to analyze a diarized conversation between a dietician and patient against a clinical rubric with 6 dimensions.

For EACH dimension:
1. Identify which sub-criteria were met (provide evidence: quote + timestamp in seconds)
2. Derive a 0-10 score based on the checklist
3. Cite specific transcript moments that justify the score

Output MUST be valid JSON matching the provided schema. Every claim must be traceable to the transcript.

Hinglish (Hindi + English code-switched) is expected in the transcript. Treat "diet plan," "khana," "sehat," and similar as equivalent concepts."""

            # Format user prompt
            user_prompt = self._format_rubric_prompt(transcript_text, metrics)

            logger.info(f"Calling Claude API for call {call_id}...")

            # Call Claude API
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )

            # Parse response
            response_text = message.content[0].text
            result = json.loads(response_text)

            logger.info(f"Claude API analysis complete for call {call_id}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response: {e}\nResponse: {response_text}")
            raise
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            raise

    def _format_transcript(self, segments: List[Dict]) -> str:
        """Format diarized segments into readable transcript."""
        lines = []
        for seg in segments:
            speaker = seg.get("speaker", "Unknown").replace("_", " ").title()
            text = seg.get("text", "")
            timestamp = seg.get("start_s", 0)
            lines.append(f"[{timestamp:.1f}s] {speaker}: {text}")

        return "\n".join(lines)

    def _format_rubric_prompt(self, transcript_text: str, metrics: dict) -> str:
        """Format the rubric prompt with actual data."""
        prompt = f"""
DIARIZED TRANSCRIPT:
{transcript_text}

CALL METRICS:
- Duration: {metrics.get('duration_seconds', 0)}s
- Dietician talk ratio: {metrics.get('dietician_talk_ratio_pct', 0)}%
- Patient talk ratio: {metrics.get('patient_talk_ratio_pct', 0)}%
- Interruptions: {metrics.get('interruption_count', 0)}
- Avg response latency: {metrics.get('avg_response_latency_seconds', 0)}s
- Time to first plan mention: {metrics.get('time_to_first_plan_mention_seconds', 'N/A')}s
- Silence %: {metrics.get('silence_pct', 0)}%

EVALUATE THESE 6 DIMENSIONS:

**Dimension 1: Discovery & Assessment (20% weight)**
Sub-criteria:
1. Medical history explored? (conditions, meds, past diagnoses mentioned)
2. Lifestyle & activity level questioned?
3. Dietary preferences & food habits discussed?
4. Patient goals discussed & aligned?
5. Allergy & dietary restriction screening done?

Score derivation: (# sub-criteria met / 5) × 10, adjusted down if questions asked but answers not incorporated into plan.

**Dimension 2: Empathy & Communication (20% weight)**
Sub-criteria:
1. Warm, empathetic tone evident? (acknowledgment of concerns, validation)
2. Conversation balance good? (from metrics: patient_talk_ratio >= 30% considered good)
3. Active listening signals present? (affirmations, paraphrasing, no interruptions)
4. Patient engagement high? (elaborated responses vs. one-word answers)
5. Overall sentiment positive or neutral? (patient frustration/confusion not evident)

Score derivation: (# sub-criteria met / 5) × 10. Extract sentiment (positive/neutral/negative) from patient turns.

**Dimension 3: Forced/Rushed Consultation Detection (15% weight, inverse-scored)**
Sub-criteria:
1. Call too short relative to typical? (<5 min unusual, <3 min very rushed)
2. Plan prescribed WITHOUT sufficient discovery? (time_to_first_plan_mention < 120s AND discovery sub-criteria < 3)
3. Dietician monologue ratio HIGH? (dietician_talk_ratio > 70%)
4. Standard discovery questions ABSENT?

If any sub-criterion triggered, score reflects risk (higher score = higher risk). Flag as "is_forced": true/false, "is_missing_discovery": true/false.

**Dimension 4: Adherence Counselling Quality (20% weight)**
Sub-criteria:
1. Motivation & encouragement provided?
2. Why adherence matters explained? (consequences if not followed, benefits explained)
3. Plan is practical & realistic? (fits patient's routine, budget, food access discussed)
4. Barriers identified & addressed? (time, cravings, social eating, cost concerns proactively handled)

Score derivation: (# sub-criteria met / 4) × 10.

**Dimension 5: Consultation Completeness (25% weight)**
Sub-criteria:
1. Goals discussed & confirmed back to patient?
2. BMI / weight status reviewed?
3. Existing medical conditions reflected in plan? (not just asked, but incorporated)
4. Follow-up guidance clear? (next appointment, check-in cadence, what to track)

Score derivation: (# sub-criteria met / 4) × 10.

**Dimension 6: Clinical Safety & Red-Flag Handling (gate, not additive)**
Sub-criteria:
1. Red flags mentioned by patient? (chest pain, disordered eating, pregnancy, uncontrolled diabetes, severe allergy)
2. If red flag detected, was it handled appropriately? (referral given, escalation, plan adjusted, NOT ignored)

Flags: "red_flag_detected": bool, "handled_appropriately": bool/null (null if no flag).

---

RESPOND WITH THIS EXACT JSON STRUCTURE (and NOTHING else - just raw JSON):
{{
  "dimension_scores": {{
    "discovery_assessment": {{
      "score": <0-10 float>,
      "evidence": [
        {{"quote": "<exact transcript quote>", "timestamp_s": <timestamp>}},
        ...
      ],
      "sub_criteria_met": {{
        "medical_history": <bool>,
        "lifestyle_activity": <bool>,
        "dietary_habits": <bool>,
        "goal_alignment": <bool>,
        "allergy_screening": <bool>
      }}
    }},
    "empathy_communication": {{
      "score": <0-10 float>,
      "evidence": [...],
      "sub_criteria_met": {{
        "empathy_tone": <bool>,
        "conversation_balance": <bool>,
        "active_listening": <bool>,
        "patient_engagement": <bool>,
        "sentiment": "positive|neutral|negative"
      }}
    }},
    "rushed_forced_detection": {{
      "score": <0-10 float>,
      "evidence": [...],
      "is_forced": <bool>,
      "is_missing_discovery": <bool>
    }},
    "adherence_counselling": {{
      "score": <0-10 float>,
      "evidence": [...],
      "sub_criteria_met": {{
        "motivation": <bool>,
        "importance_explained": <bool>,
        "practical_implementation": <bool>,
        "barriers_addressed": <bool>
      }}
    }},
    "consultation_completeness": {{
      "score": <0-10 float>,
      "evidence": [...],
      "sub_criteria_met": {{
        "goals_documented": <bool>,
        "bmi_reviewed": <bool>,
        "conditions_incorporated": <bool>,
        "followup_shared": <bool>
      }}
    }},
    "clinical_safety": {{
      "score": 0,
      "evidence": [...],
      "red_flag_detected": <bool>,
      "handled_appropriately": <bool|null>
    }}
  }},
  "feedback_summary": [
    "<one natural-language feedback bullet>",
    "<another bullet>",
    ...
  ]
}}

Be concise in evidence quotes (max 50 words each). Output MUST be valid JSON.
"""
        return prompt
