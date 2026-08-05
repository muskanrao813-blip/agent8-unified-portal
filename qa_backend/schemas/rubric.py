from pydantic import BaseModel
from typing import Optional, List


class Evidence(BaseModel):
    quote: str
    timestamp_s: float


class DimensionScore(BaseModel):
    score: float
    evidence: List[Evidence]
    sub_criteria_met: dict[str, bool]
    sentiment: Optional[str] = None
    is_forced: Optional[bool] = None
    is_missing_discovery: Optional[bool] = None
    red_flag_detected: Optional[bool] = None
    handled_appropriately: Optional[bool] = None


class Metrics(BaseModel):
    dietician_talk_ratio_pct: float
    patient_talk_ratio_pct: float
    interruption_count: int
    avg_response_latency_seconds: float
    time_to_first_plan_mention_seconds: Optional[float]
    silence_pct: float
    off_topic_time_pct: float


class QAFlag(BaseModel):
    flag_type: str
    triggered: bool
    detail: Optional[str]


class RubricAnalysisResponse(BaseModel):
    call_id: str
    dietician_id: str
    dietician_name: str
    patient_id: str
    call_datetime: str
    call_duration_seconds: int
    metrics: Metrics
    dimension_scores: dict[str, DimensionScore]
    overall_weighted_score: float
    qa_flags: List[QAFlag]
    feedback_summary: List[str]
    retraining_recommended: bool
    retraining_reason: Optional[str]
