"""Local rule-based analyzer for real analysis without API keys."""

import logging
import re
from typing import Dict, List
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class LocalAnalyzerProvider(LLMProvider):
    """Analyzes transcripts using intelligent rules - no API key needed!"""

    def analyze_all_dimensions(
        self,
        transcript_segments: List[Dict],
        metrics: Dict,
        call_id: str,
        dietician_name: str,
        patient_id: str
    ) -> Dict:
        """Analyze using transcript rules and metrics."""
        try:
            logger.info(f"Analyzing call {call_id} with local rules...")

            # Combine all text
            full_text = " ".join([s.get("text", "") for s in transcript_segments])

            # Analyze each dimension
            discovery = self._analyze_discovery(full_text, transcript_segments)
            empathy = self._analyze_empathy(full_text, metrics)
            rushed = self._analyze_rushed(metrics, discovery)
            adherence = self._analyze_adherence(full_text, transcript_segments)
            completeness = self._analyze_completeness(full_text, metrics)
            safety = self._analyze_safety(full_text)

            logger.info(f"Analysis complete for {call_id}: discovery={discovery['score']}, empathy={empathy['score']}")

            return {
                "dimension_scores": {
                    "discovery_assessment": discovery,
                    "empathy_communication": empathy,
                    "rushed_forced_detection": rushed,
                    "adherence_counselling": adherence,
                    "consultation_completeness": completeness,
                    "clinical_safety": safety
                },
                "feedback_summary": self._generate_feedback(discovery, empathy, rushed, adherence, completeness, safety)
            }

        except Exception as e:
            logger.error(f"Error in local analysis: {e}")
            raise

    def _analyze_discovery(self, text: str, segments: List[Dict]) -> Dict:
        """Analyze discovery & assessment dimension."""
        score = 5.0  # Base score

        # Keywords for each criterion
        medical_keywords = ["condition", "disease", "diabetes", "hypertension", "medication", "medicine", "health", "illness"]
        lifestyle_keywords = ["exercise", "activity", "work", "sleep", "routine", "sedentary", "active"]
        dietary_keywords = ["food", "diet", "eating", "prefer", "like", "dislike", "allergic", "allergy", "vegetarian", "non-veg"]
        goal_keywords = ["goal", "target", "want", "achieve", "hope", "plan", "weight", "lose", "gain"]
        allergy_keywords = ["allergy", "allergic", "intolerant", "allergy", "shellfish", "nuts", "gluten"]

        text_lower = text.lower()

        # Count criteria met
        criteria_met = 0
        sub_criteria = {
            "medical_history": False,
            "lifestyle_activity": False,
            "dietary_habits": False,
            "goal_alignment": False,
            "allergy_screening": False
        }

        if any(kw in text_lower for kw in medical_keywords):
            criteria_met += 1
            sub_criteria["medical_history"] = True
            score += 1.5

        if any(kw in text_lower for kw in lifestyle_keywords):
            criteria_met += 1
            sub_criteria["lifestyle_activity"] = True
            score += 1.5

        if any(kw in text_lower for kw in dietary_keywords):
            criteria_met += 1
            sub_criteria["dietary_habits"] = True
            score += 1.5

        if any(kw in text_lower for kw in goal_keywords):
            criteria_met += 1
            sub_criteria["goal_alignment"] = True
            score += 1.5

        if any(kw in text_lower for kw in allergy_keywords):
            criteria_met += 1
            sub_criteria["allergy_screening"] = True
            score += 1.5

        # Bonus for conversation length (indicates thorough discussion)
        num_segments = len(segments)
        if num_segments > 5:
            score += 0.5
        if num_segments > 10:
            score += 0.5

        score = min(10, max(0, score))

        # Generate evidence
        evidence = []
        for seg in segments[:3]:
            if any(kw in seg.get("text", "").lower() for kw in medical_keywords + lifestyle_keywords + dietary_keywords + goal_keywords):
                evidence.append({
                    "quote": seg.get("text", "")[:80],
                    "timestamp_s": seg.get("start_s", 0)
                })

        return {
            "score": round(score, 1),
            "evidence": evidence,
            "sub_criteria_met": sub_criteria
        }

    def _analyze_empathy(self, text: str, metrics: Dict) -> Dict:
        """Analyze empathy & communication dimension."""
        score = 5.0

        # Keywords for empathy
        empathy_keywords = ["understand", "feel", "concern", "worried", "acknowledge", "appreciate", "thank", "good", "nice", "great"]
        listening_keywords = ["yes", "right", "exactly", "sure", "okay", "absolutely", "indeed"]

        text_lower = text.lower()

        # Check empathy tone
        empathy_count = sum(1 for kw in empathy_keywords if kw in text_lower)
        if empathy_count > 0:
            score += 2
        if empathy_count > 2:
            score += 1

        # Check conversation balance (from metrics)
        patient_talk = metrics.get("patient_talk_ratio_pct", 0)
        if patient_talk >= 30:
            score += 1.5
        elif patient_talk >= 20:
            score += 0.5

        # Dietician shouldn't monopolize
        dietician_talk = metrics.get("dietician_talk_ratio_pct", 0)
        if dietician_talk < 70:
            score += 1

        # Check interruptions (lower is better)
        interruptions = metrics.get("interruption_count", 0)
        if interruptions == 0:
            score += 1
        elif interruptions > 5:
            score -= 1

        # Check sentiment through words
        positive_words = ["good", "great", "perfect", "wonderful", "thank", "happy"]
        negative_words = ["bad", "angry", "frustrated", "upset", "confused", "worried"]

        positive_count = sum(1 for w in positive_words if w in text_lower)
        negative_count = sum(1 for w in negative_words if w in text_lower)

        sentiment = "positive" if positive_count > negative_count else "neutral" if negative_count == 0 else "negative"

        if sentiment == "positive":
            score += 1

        score = min(10, max(0, score))

        return {
            "score": round(score, 1),
            "evidence": [],
            "sub_criteria_met": {
                "empathy_tone": empathy_count > 0,
                "conversation_balance": patient_talk >= 30,
                "active_listening": listening_keywords[0] in text_lower,
                "patient_engagement": patient_talk > 0,
                "sentiment": sentiment
            }
        }

    def _analyze_rushed(self, metrics: Dict, discovery: Dict) -> Dict:
        """Analyze if consultation was rushed/forced."""
        score = 3.0  # Base (low risk)

        duration = metrics.get("duration_seconds", 0)
        time_to_plan = metrics.get("time_to_first_plan_mention_seconds", 0)
        dietician_talk = metrics.get("dietician_talk_ratio_pct", 0)
        discovery_score = discovery.get("score", 0)

        # Short calls are risky
        if duration < 300:
            score += 1
        if duration < 180:
            score += 2

        # Plan too early without discovery
        if time_to_plan < 120 and discovery_score < 5:
            score += 2

        # Dietician talks too much
        if dietician_talk > 70:
            score += 1.5
        if dietician_talk > 85:
            score += 1

        score = min(10, max(0, score))

        return {
            "score": round(score, 1),
            "evidence": [],
            "is_forced": score > 6,
            "is_missing_discovery": discovery_score < 5
        }

    def _analyze_adherence(self, text: str, segments: List[Dict]) -> Dict:
        """Analyze adherence counselling quality."""
        score = 5.0

        adherence_keywords = ["follow", "stick", "keep", "maintain", "continue", "important", "must", "should", "try", "effort"]
        barrier_keywords = ["time", "busy", "cost", "expensive", "afford", "like", "taste", "difficult", "hard", "challenge"]
        practical_keywords = ["easy", "simple", "manageable", "routine", "habit", "daily", "weekly"]

        text_lower = text.lower()

        # Check adherence emphasis
        adherence_count = sum(1 for kw in adherence_keywords if kw in text_lower)
        if adherence_count > 0:
            score += 1.5
        if adherence_count > 2:
            score += 1

        # Check if barriers discussed
        barrier_count = sum(1 for kw in barrier_keywords if kw in text_lower)
        if barrier_count > 0:
            score += 1.5

        # Check if practical solutions offered
        practical_count = sum(1 for kw in practical_keywords if kw in text_lower)
        if practical_count > 0:
            score += 1.5

        # Longer consultation = more adherence discussion
        if len(segments) > 10:
            score += 1

        score = min(10, max(0, score))

        return {
            "score": round(score, 1),
            "evidence": [],
            "sub_criteria_met": {
                "motivation": adherence_count > 0,
                "importance_explained": adherence_count > 1,
                "practical_implementation": practical_count > 0,
                "barriers_addressed": barrier_count > 0
            }
        }

    def _analyze_completeness(self, text: str, metrics: Dict) -> Dict:
        """Analyze consultation completeness."""
        score = 5.0

        goal_keywords = ["goal", "target", "achieve", "plan"]
        bmi_keywords = ["weight", "bmi", "kg", "pounds", "thin", "fat", "obese"]
        condition_keywords = ["condition", "health", "status", "disease", "diabetes", "blood pressure"]
        followup_keywords = ["follow", "next", "appointment", "week", "month", "check", "revisit"]

        text_lower = text.lower()

        # Goals documented
        if any(kw in text_lower for kw in goal_keywords):
            score += 2

        # BMI/weight reviewed
        if any(kw in text_lower for kw in bmi_keywords):
            score += 1.5

        # Conditions incorporated
        if any(kw in text_lower for kw in condition_keywords):
            score += 1.5

        # Follow-up clear
        if any(kw in text_lower for kw in followup_keywords):
            score += 1.5

        # Longer consultation = more comprehensive
        if metrics.get("duration_seconds", 0) > 600:
            score += 1

        score = min(10, max(0, score))

        return {
            "score": round(score, 1),
            "evidence": [],
            "sub_criteria_met": {
                "goals_documented": any(kw in text_lower for kw in goal_keywords),
                "bmi_reviewed": any(kw in text_lower for kw in bmi_keywords),
                "conditions_incorporated": any(kw in text_lower for kw in condition_keywords),
                "followup_shared": any(kw in text_lower for kw in followup_keywords)
            }
        }

    def _analyze_safety(self, text: str) -> Dict:
        """Analyze clinical safety."""
        score = 0.0

        red_flag_keywords = ["chest", "pain", "eating", "disorder", "pregnant", "diabetes", "allergy", "severe", "emergency"]
        handling_keywords = ["refer", "doctor", "hospital", "urgent", "immediately", "escalate", "consult"]

        text_lower = text.lower()

        red_flag_detected = any(kw in text_lower for kw in red_flag_keywords)
        handled = any(kw in text_lower for kw in handling_keywords) if red_flag_detected else None

        return {
            "score": 0,
            "evidence": [],
            "red_flag_detected": red_flag_detected,
            "handled_appropriately": handled
        }

    def _generate_feedback(self, discovery, empathy, rushed, adherence, completeness, safety) -> List[str]:
        """Generate feedback bullets."""
        feedback = []

        # Discovery feedback
        if discovery["score"] < 5:
            feedback.append("Focus more on understanding patient's medical history, lifestyle, and dietary habits before suggesting a plan.")
        elif discovery["score"] >= 8:
            feedback.append("Excellent! You did a thorough job exploring patient's background and needs.")

        # Empathy feedback
        if empathy["score"] < 5:
            feedback.append("Work on building rapport - acknowledge patient concerns and show more active listening.")
        if empathy["sub_criteria_met"]["sentiment"] == "negative":
            feedback.append("Patient seemed frustrated. Try to clarify points and ensure they feel heard.")

        # Rushed feedback
        if rushed["is_forced"]:
            feedback.append("Avoid prescribing the diet plan too early. Spend more time on discovery first.")
        if rushed["score"] > 6:
            feedback.append("This consultation felt rushed. Allow more time for patient to share and ask questions.")

        # Adherence feedback
        if adherence["score"] < 5:
            feedback.append("Strengthen adherence discussion - explain why following the plan is important and help identify barriers.")

        # Completeness feedback
        if completeness["score"] < 5:
            feedback.append("Ensure consultation is complete - confirm goals, review health status, and clarify follow-up steps.")

        # Safety feedback
        if safety["red_flag_detected"] and not safety["handled_appropriately"]:
            feedback.append("IMPORTANT: A potential health concern was mentioned but not properly addressed. Escalate to physician.")

        if not feedback:
            feedback.append("Good consultation overall. Continue maintaining this quality in future calls.")

        return feedback
