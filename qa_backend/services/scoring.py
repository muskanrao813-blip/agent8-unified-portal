"""Deterministic scoring, flagging, and feedback generation."""

import logging
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from app.db import models

logger = logging.getLogger(__name__)


def compute_weighted_score(
    dimension_scores: Dict[str, float],
    clinical_safety_triggered: bool = False
) -> float:
    """Compute overall weighted score (0-100) from ClinicalAnalyzer dimension scores.

    ClinicalAnalyzer returns: greeting, empathy, compliance, technical (0-100 each).
    Weights sum to 1.0.
    """
    # Map from ClinicalAnalyzer dimension names → weights
    weights = {
        "greeting":   0.15,
        "empathy":    0.25,
        "compliance": 0.35,
        "technical":  0.25,
    }

    weighted_sum = 0.0
    for dim, weight in weights.items():
        score = dimension_scores.get(dim, 0.0)
        weighted_sum += score * weight

    # Clinical safety gate: if triggered and mishandled, cap at 40 out of 100
    if clinical_safety_triggered:
        weighted_sum = min(weighted_sum, 40.0)

    return round(weighted_sum, 2)


def evaluate_flags(
    metrics: Dict,
    dimension_scores: Dict,
    rubric_data: Dict,
    db: Session,
    call: models.Call
) -> List[Dict]:
    """Evaluate deterministic QA flags."""
    flags = []

    # Extract sub-criteria from rubric data
    discovery_subcriteria = rubric_data.get("dimension_scores", {}).get("discovery_assessment", {}).get("sub_criteria_met", {})
    adherence_subcriteria = rubric_data.get("dimension_scores", {}).get("adherence_counselling", {}).get("sub_criteria_met", {})
    rushed_data = rubric_data.get("dimension_scores", {}).get("rushed_forced_detection", {})
    safety_data = rubric_data.get("dimension_scores", {}).get("clinical_safety", {})

    # 1. Forced Consultation
    forced = (
        (metrics.get("time_to_first_plan_mention_seconds") or 999) < 120 and
        sum(1 for v in discovery_subcriteria.values() if v) < 3
    )
    flags.append({
        "flag_type": "Forced Consultation",
        "triggered": forced,
        "detail": "Diet plan prescribed within 2 min with insufficient discovery" if forced else None,
    })

    # 2. Missing Discovery
    discovery_count = sum(1 for v in discovery_subcriteria.values() if v)
    missing_discovery = discovery_count < 3
    flags.append({
        "flag_type": "Missing Discovery",
        "triggered": missing_discovery,
        "detail": f"Only {discovery_count}/5 discovery sub-criteria met" if missing_discovery else None,
    })

    # 3. Low Engagement
    low_engagement = metrics.get("patient_talk_ratio_pct", 0) < 20
    flags.append({
        "flag_type": "Low Engagement",
        "triggered": low_engagement,
        "detail": f"Patient talk ratio {metrics.get('patient_talk_ratio_pct', 0)}% (threshold: <20%)" if low_engagement else None,
    })

    # 4. Poor Adherence Counselling
    adherence_count = sum(1 for v in adherence_subcriteria.values() if v)
    poor_adherence = adherence_count == 0
    flags.append({
        "flag_type": "Poor Adherence Counselling",
        "triggered": poor_adherence,
        "detail": "No adherence counselling sub-criteria met" if poor_adherence else None,
    })

    # 5. Off-Topic/Non-Consultative Time
    off_topic = metrics.get("off_topic_time_pct", 0) > 25
    flags.append({
        "flag_type": "Off-Topic/Non-Consultative Time",
        "triggered": off_topic,
        "detail": f"Off-topic time {metrics.get('off_topic_time_pct', 0)}% (threshold: >25%)" if off_topic else None,
    })

    # 6. Appointment Not Delivered
    # Placeholder: would need word count from transcript
    appointment_not_delivered = False  # TODO: implement patient word count check
    flags.append({
        "flag_type": "Appointment Not Delivered",
        "triggered": appointment_not_delivered,
        "detail": "Patient word count too low or near-zero clinical content" if appointment_not_delivered else None,
    })

    # 7. Clinical Safety Concern
    red_flag = safety_data.get("red_flag_detected", False)
    handled = safety_data.get("handled_appropriately", True)
    clinical_safety = red_flag and not handled
    flags.append({
        "flag_type": "Clinical Safety Concern",
        "triggered": clinical_safety,
        "detail": "Red flag detected and not appropriately handled/escalated" if clinical_safety else None,
    })

    # 8. Templated/Generic Plan Suspected
    templated = False  # v2 feature: requires historical comparison
    flags.append({
        "flag_type": "Templated/Generic Plan Suspected",
        "triggered": templated,
        "detail": "Plan appears templated/copied from prior calls (v2 feature)" if templated else None,
    })

    return flags


def generate_retraining_recommendation(
    overall_score: float,
    flags: List[Dict],
    dietician_id: str,
    db: Session
) -> Tuple[bool, str]:
    """Determine if retraining is recommended based on score and pattern."""
    # Single call triggers
    if overall_score < 6.0:
        return True, f"Overall score {overall_score} below threshold (6.0)"

    clinical_safety_triggered = any(f["flag_type"] == "Clinical Safety Concern" and f["triggered"] for f in flags)
    if clinical_safety_triggered:
        return True, "Clinical safety concern detected"

    # Pattern-based: check last 10 calls for recurring flags
    recent_calls = (
        db.query(models.Call)
        .filter(models.Call.dietician_id == dietician_id)
        .order_by(models.Call.call_datetime.desc())
        .limit(10)
        .all()
    )

    forced_count = 0
    missing_discovery_count = 0

    for call in recent_calls:
        qa_flags = db.query(models.QAFlag).filter(models.QAFlag.call_id == call.id).all()
        for flag in qa_flags:
            if flag.flag_type == "Forced Consultation" and flag.triggered:
                forced_count += 1
            elif flag.flag_type == "Missing Discovery" and flag.triggered:
                missing_discovery_count += 1

    if forced_count >= 3 or missing_discovery_count >= 3:
        return True, f"Pattern detected: {max(forced_count, missing_discovery_count)}/10 calls flagged"

    return False, None


def generate_feedback_bullets(
    dimension_scores: Dict,
    rubric_data: Dict,
    flags: List[Dict]
) -> List[str]:
    """Generate natural-language feedback bullets."""
    bullets = []

    # Discovery feedback
    discovery_score = dimension_scores.get("discovery_assessment", 0)
    if discovery_score < 5:
        bullets.append("Strengthen discovery questioning: ask about medical history, lifestyle, and dietary preferences before prescribing.")
    elif discovery_score >= 8:
        bullets.append("Excellent discovery and assessment work — good coverage of patient context.")

    # Empathy feedback
    empathy_score = dimension_scores.get("empathy_communication", 0)
    empathy_data = rubric_data.get("dimension_scores", {}).get("empathy_communication", {})
    sentiment = empathy_data.get("sub_criteria_met", {}).get("sentiment", "neutral")

    if empathy_score < 5:
        bullets.append("Increase empathy: validate patient concerns, use active listening cues, balance conversation more.")
    if sentiment == "negative":
        bullets.append("Patient showed signs of frustration or confusion — clarify plan and check understanding.")

    # Adherence feedback
    adherence_score = dimension_scores.get("adherence_counselling", 0)
    if adherence_score < 5:
        bullets.append("Strengthen adherence counselling: explain why the plan matters, discuss barriers, make it realistic for patient lifestyle.")

    # Completeness feedback
    completeness_score = dimension_scores.get("consultation_completeness", 0)
    if completeness_score < 5:
        bullets.append("Ensure completeness: confirm goals back to patient, review BMI/weight status, clarify next steps and follow-up.")

    # Flag-based feedback
    if any(f["triggered"] for f in flags if f["flag_type"] == "Forced Consultation"):
        bullets.append("Avoid prescribing plan too early — spend more time understanding patient needs first.")

    if any(f["triggered"] for f in flags if f["flag_type"] == "Low Engagement"):
        bullets.append("Increase patient participation: ask open-ended questions, listen more, reduce your own talk time.")

    return bullets if bullets else ["Call meets baseline standards for consultation quality."]
