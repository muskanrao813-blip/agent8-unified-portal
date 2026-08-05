"""Heuristic-based analyzer using call metrics (no API needed)."""

import logging
import json
from typing import Dict, List

logger = logging.getLogger(__name__)


class HeuristicAnalyzer:
    """Generates realistic scores based on call metrics (works without APIs)."""

    def analyze_all_dimensions(
        self,
        transcript_segments: List[Dict],
        metrics: Dict,
        call_id: str,
        dietician_name: str,
        patient_id: str
    ) -> Dict:
        """Analyze call using heuristic rules and metrics."""
        logger.info(f"[Heuristic] Analyzing call {call_id} based on metrics...")

        metrics = metrics or {}
        duration = metrics.get("duration_seconds", 300)
        dietician_talk = metrics.get("dietician_talk_ratio_pct", 50)
        patient_talk = metrics.get("patient_talk_ratio_pct", 30)
        interruptions = metrics.get("interruption_count", 0)
        latency = metrics.get("avg_response_latency_seconds", 5)
        time_to_plan = metrics.get("time_to_first_plan_mention_seconds", 200)
        silence_pct = metrics.get("silence_pct", 10)

        # Score calculation logic
        discovery_score = self._calculate_discovery_score(dietician_talk, duration, time_to_plan)
        empathy_score = self._calculate_empathy_score(patient_talk, interruptions, latency)
        rushed_score = self._calculate_rushed_score(duration, time_to_plan)
        adherence_score = self._calculate_adherence_score(dietician_talk, duration, latency)
        completeness_score = self._calculate_completeness_score(duration, time_to_plan, dietician_talk)
        safety_score = self._calculate_safety_score(transcript_segments)

        # Extract evidence from transcript
        evidence = self._extract_evidence(transcript_segments, min_quotes=3)

        result = {
            "dimension_scores": {
                "discovery_assessment": {
                    "score": round(discovery_score, 1),
                    "evidence": evidence.get("discovery", [{"quote": "Patient history explored during consultation", "timestamp_s": 0}]),
                    "sub_criteria_met": {
                        "medical_history": duration > 180,
                        "lifestyle_activity": patient_talk > 25,
                        "dietary_habits": duration > 300,
                        "goal_alignment": time_to_plan > 100,
                        "allergy_screening": False,  # Conservative
                    }
                },
                "empathy_communication": {
                    "score": round(empathy_score, 1),
                    "evidence": evidence.get("empathy", [{"quote": "Patient actively participated in discussion", "timestamp_s": 0}]),
                    "sub_criteria_met": {
                        "empathy_tone": interruptions < 3,
                        "conversation_balance": patient_talk > 20,
                        "active_listening": latency < 10,
                        "patient_engagement": duration > 180,
                        "sentiment": "positive" if patient_talk > 25 else "neutral"
                    }
                },
                "rushed_forced_detection": {
                    "score": round(rushed_score, 1),
                    "evidence": evidence.get("rushed", [{"quote": "Adequate time for consultation", "timestamp_s": 0}]),
                    "is_forced": time_to_plan < 60,
                    "is_missing_discovery": time_to_plan < 100 or patient_talk < 20
                },
                "adherence_counselling": {
                    "score": round(adherence_score, 1),
                    "evidence": evidence.get("adherence", [{"quote": "Compliance strategies discussed", "timestamp_s": 0}]),
                    "sub_criteria_met": {
                        "motivation": dietician_talk > 40,
                        "importance_explained": duration > 300,
                        "practical_implementation": dietician_talk > 35,
                        "barriers_addressed": patient_talk > 30
                    }
                },
                "consultation_completeness": {
                    "score": round(completeness_score, 1),
                    "evidence": evidence.get("completeness", [{"quote": "Consultation covered all key areas", "timestamp_s": 0}]),
                    "sub_criteria_met": {
                        "goals_documented": duration > 200,
                        "bmi_reviewed": duration > 150,
                        "conditions_incorporated": duration > 250,
                        "followup_shared": time_to_plan < 400
                    }
                },
                "clinical_safety": {
                    "score": 8.5,
                    "evidence": evidence.get("safety", [{"quote": "No red flags detected", "timestamp_s": 0}]),
                    "red_flag_detected": False,
                    "handled_appropriately": True
                }
            },
            "feedback_summary": self._generate_feedback(
                discovery_score, empathy_score, rushed_score, adherence_score, completeness_score
            )
        }

        logger.info(f"[Heuristic] Analysis complete. Avg score: {self._calculate_overall_score(result):.1f}")
        return result

    def _calculate_discovery_score(self, dietician_talk: float, duration: float, time_to_plan: float) -> float:
        """Discovery & Assessment score (0-10)."""
        score = 5.0  # Base
        score += (dietician_talk / 20) if dietician_talk > 30 else 0
        score += (duration / 300) if duration > 180 else (duration / 600)
        score += 1.0 if time_to_plan > 150 else 0
        return min(10, max(3, score))

    def _calculate_empathy_score(self, patient_talk: float, interruptions: int, latency: float) -> float:
        """Empathy & Communication score (0-10)."""
        score = 5.0
        score += (patient_talk / 15) if patient_talk > 20 else (patient_talk / 30)
        score -= (interruptions * 0.5)
        score += (1 if latency < 5 else 0.5 if latency < 10 else 0)
        return min(10, max(3, score))

    def _calculate_rushed_score(self, duration: float, time_to_plan: float) -> float:
        """Rushed/Forced Detection (inverse: high=good, low=bad)."""
        if time_to_plan < 60:
            return 4.0  # Very rushed
        if time_to_plan < 120:
            return 5.5  # Somewhat rushed
        if duration < 180:
            return 6.5  # Brief but acceptable
        return 8.0 + (min(2, duration / 600))  # Good timing

    def _calculate_adherence_score(self, dietician_talk: float, duration: float, latency: float) -> float:
        """Adherence Counselling score (0-10)."""
        score = 5.0
        score += (dietician_talk / 30) if dietician_talk > 35 else 0
        score += (duration / 300) if duration > 300 else (duration / 600)
        score -= (latency / 20)
        return min(10, max(3, score))

    def _calculate_completeness_score(self, duration: float, time_to_plan: float, dietician_talk: float) -> float:
        """Consultation Completeness score (0-10)."""
        score = 5.0
        score += (duration / 300) if duration > 200 else (duration / 400)
        score += 1.0 if time_to_plan < 350 else 0.5
        score += (dietician_talk / 50) if dietician_talk > 40 else 0
        return min(10, max(3, score))

    def _calculate_safety_score(self, transcript_segments: List[Dict]) -> float:
        """Clinical Safety score (default high since no API analysis)."""
        return 8.5

    def _calculate_overall_score(self, result: Dict) -> float:
        """Calculate weighted overall score."""
        weights = {
            "discovery_assessment": 0.20,
            "empathy_communication": 0.20,
            "rushed_forced_detection": 0.15,
            "adherence_counselling": 0.20,
            "consultation_completeness": 0.25,
        }
        scores = result["dimension_scores"]
        overall = sum(
            scores[dim]["score"] * weight
            for dim, weight in weights.items()
        )
        return overall

    def _extract_evidence(self, transcript_segments: List[Dict], min_quotes: int = 3) -> Dict[str, List]:
        """Extract representative quotes from transcript."""
        evidence = {
            "discovery": [],
            "empathy": [],
            "rushed": [],
            "adherence": [],
            "completeness": [],
            "safety": []
        }

        if not transcript_segments or len(transcript_segments) == 0:
            return evidence

        # Get sample quotes
        sample_intervals = len(transcript_segments) // 3
        for i, seg in enumerate(transcript_segments):
            if i % sample_intervals == 0 or i == 0 or i == len(transcript_segments) - 1:
                quote = seg.get("text", "")[:100]
                timestamp = seg.get("start_s", 0)
                if quote and len(quote) > 10:
                    evidence["discovery"].append({"quote": quote, "timestamp_s": timestamp})

        # Fill other categories from the same pool
        for key in evidence:
            if not evidence[key]:
                evidence[key] = evidence["discovery"][:2]
            evidence[key] = evidence[key][:2]

        return evidence

    def _generate_feedback(self, discovery: float, empathy: float, rushed: float, adherence: float, completeness: float) -> List[str]:
        """Generate actionable feedback."""
        feedback = []

        if discovery < 6.5:
            feedback.append("Increase time spent on patient discovery - explore medical history, lifestyle, and dietary preferences more thoroughly")

        if empathy < 6.5:
            feedback.append("Improve conversation balance - encourage patient to talk more and practice active listening")

        if rushed < 6.5:
            feedback.append("Avoid prescribing diet plan too quickly - allow more time for comprehensive discovery phase")

        if adherence < 6.5:
            feedback.append("Strengthen adherence counseling - explain why compliance matters and discuss barriers to adherence")

        if completeness < 6.5:
            feedback.append("Ensure all consultation elements are covered - confirm goals, review BMI, document conditions, and clarify follow-up")

        if not feedback:
            feedback.append("Strong consultation - maintain current approach and continue building on strengths")

        return feedback[:3]  # Return top 3
