"""Abstract LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, List


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def analyze_all_dimensions(
        self,
        transcript_segments: List[Dict],
        metrics: Dict,
        call_id: str,
        dietician_name: str,
        patient_id: str
    ) -> Dict:
        """
        Analyze transcript against all 6 rubric dimensions.

        Returns structured JSON matching Section 4 schema:
        {
            "dimension_scores": {
                "discovery_assessment": {...},
                "empathy_communication": {...},
                "rushed_forced_detection": {...},
                "adherence_counselling": {...},
                "consultation_completeness": {...},
                "clinical_safety": {...}
            },
            "feedback_summary": [...]
        }
        """
        pass
