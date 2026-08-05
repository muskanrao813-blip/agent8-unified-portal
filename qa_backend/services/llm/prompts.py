"""System and rubric prompts for LLM analysis."""

SYSTEM_PROMPT = """You are an expert healthcare quality analyst specializing in evaluating dietician consultation transcripts.

Your task is to analyze a diarized conversation between a dietician and patient against a clinical rubric with 6 dimensions.

For EACH dimension:
1. Identify which sub-criteria were met (provide evidence: quote + timestamp in seconds)
2. Derive a 0-10 score based on the checklist
3. Cite specific transcript moments that justify the score

Output MUST be valid JSON matching the provided schema. Every claim must be traceable to the transcript.

Hinglish (Hindi + English code-switched) is expected in the transcript. Treat "diet plan," "khana," "sehat," and similar as equivalent concepts.
"""

RUBRIC_PROMPT = """
DIARIZED TRANSCRIPT:
{transcript_text}

CALL METRICS:
- Duration: {duration_seconds}s
- Dietician talk ratio: {dietician_talk_ratio_pct}%
- Patient talk ratio: {patient_talk_ratio_pct}%
- Interruptions: {interruption_count}
- Avg response latency: {avg_response_latency_seconds}s
- Time to first plan mention: {time_to_first_plan_mention_seconds}s
- Silence %: {silence_pct}%

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

RESPOND WITH THIS EXACT JSON STRUCTURE:
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

Be concise in evidence quotes (max 50 words each). Output MUST be valid JSON — test before responding.
"""

def format_rubric_prompt(transcript_text: str, metrics: dict) -> str:
    """Format the rubric prompt with actual data."""
    return RUBRIC_PROMPT.format(
        transcript_text=transcript_text,
        duration_seconds=metrics.get("duration_seconds", 0),
        dietician_talk_ratio_pct=metrics.get("dietician_talk_ratio_pct", 0),
        patient_talk_ratio_pct=metrics.get("patient_talk_ratio_pct", 0),
        interruption_count=metrics.get("interruption_count", 0),
        avg_response_latency_seconds=metrics.get("avg_response_latency_seconds", 0),
        time_to_first_plan_mention_seconds=metrics.get("time_to_first_plan_mention_seconds", "N/A"),
        silence_pct=metrics.get("silence_pct", 0),
    )
