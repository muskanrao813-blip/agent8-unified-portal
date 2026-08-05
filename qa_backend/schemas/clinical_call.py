"""Clinical call analysis schemas matching FE requirements."""

from pydantic import BaseModel
from typing import List, Dict, Optional


class TranscriptTurn(BaseModel):
    """Transcript turn with clinical analysis."""
    id: str
    speaker: str  # 'agent' or 'patient'
    speaker_name: str
    timestamp: str
    text: str
    is_critical: Optional[bool] = False
    critical_badge: Optional[str] = None  # 'HIPAA', 'SAFETY', etc.
    tags: Optional[List[str]] = None  # ['positive', 'concern', 'critical']
    warning: Optional[str] = None
    ai_catch: Optional[str] = None


class QAAlert(BaseModel):
    """QA Alert for SOP violations and concerns."""
    id: str
    title: str
    description: str
    severity: str  # 'critical', 'warning', 'info'
    status: str  # 'active', 'resolved'


class CallScore(BaseModel):
    """Individual call score dimensions."""
    greeting: float  # 0-100
    empathy: float  # 0-100
    compliance: float  # 0-100 (SOP)
    technical: float  # 0-100


class SOPCompliance(BaseModel):
    """SOP compliance assessment."""
    compliant: bool
    score: float  # 0-100
    violations: List[Dict] = []
    checks: Dict[str, bool] = {}  # check_name: passed


class CallInsights(BaseModel):
    """Clinical insights and recommendations."""
    what_went_well: List[str]
    areas_for_improvement: List[str]
    summary: str
    training_gaps: List[Dict] = []  # type, title, description, urgency


class ClinicalCallResponse(BaseModel):
    """Complete clinical call analysis response."""
    id: str
    patient_name: str
    dietician_name: str
    date: str
    duration: str
    status: str  # 'completed', 'processing', 'waiting'

    # Scores and compliance
    scores: CallScore
    overall_score: float  # Weighted average
    sop_compliance: SOPCompliance
    sop_compliant: bool
    sop_compliance_score: float

    # QA data
    qa_alerts: List[QAAlert]
    critical_alerts_count: int

    # Clinical analysis
    transcript: List[TranscriptTurn]
    insights: CallInsights

    # Metadata
    metrics: Dict = {}
    tags: Dict[str, List[str]] = {}  # turn_id: [tags]

    class Config:
        from_attributes = True


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics."""
    total_calls: int
    avg_quality_score: float
    sop_compliance_percentage: float
    critical_alerts_count: int
    calls_this_month: int
    team_size: int


class DieticianPerformanceResponse(BaseModel):
    """Dietician performance summary."""
    id: str
    name: str
    avg_score: float
    sop_compliance_score: float
    total_calls: int
    trend_percentage: float
    trend_direction: str  # 'up', 'down', 'flat'
    ai_status: str  # 'Exceeding Goals', 'Training Required', etc.
    sop_breaches: int


def transform_call_to_clinical_response(call_db, analysis: Dict) -> Dict:
    """Transform DB call and analysis to FE clinical response."""
    scores = analysis.get("scores", {})
    sop = analysis.get("sop_compliance", {})
    alerts = analysis.get("qa_alerts", [])
    insights = analysis.get("insights", {})

    # Calculate overall score (weighted average)
    overall_score = (
        scores.get("greeting", 0) * 0.25 +  # greeting weight
        scores.get("empathy", 0) * 0.25 +    # empathy weight
        scores.get("compliance", 0) * 0.20 + # compliance weight
        scores.get("technical", 0) * 0.30    # technical weight
    )

    return {
        "id": str(call_db.id),
        "patient_name": call_db.patient_name or "Unknown",
        "dietician_name": call_db.dietician.name if call_db.dietician else "Unknown",
        "date": call_db.call_datetime.isoformat() if call_db.call_datetime else "",
        "duration": f"{call_db.call_duration_seconds // 60}:{call_db.call_duration_seconds % 60:02d}" if call_db.call_duration_seconds else "0:00",
        "status": str(call_db.status).split('.')[-1],  # Extract enum value
        "scores": {
            "greeting": scores.get("greeting", 0),
            "empathy": scores.get("empathy", 0),
            "compliance": scores.get("compliance", 0),
            "technical": scores.get("technical", 0)
        },
        "overall_score": round(overall_score, 2),
        "sop_compliance": {
            "compliant": sop.get("compliant", True),
            "score": sop.get("score", 0),
            "violations": sop.get("violations", []),
            "checks": {v.get("check", "Unknown"): not v.get("violated", False) for v in sop.get("violations", [])}
        },
        "sop_compliant": sop.get("compliant", True),
        "sop_compliance_score": sop.get("score", 0),
        "qa_alerts": alerts,
        "critical_alerts_count": len([a for a in alerts if a.get("severity") == "critical"]),
        "insights": {
            "what_went_well": insights.get("whatWentWell", []),
            "areas_for_improvement": insights.get("areasForImprovement", []),
            "summary": insights.get("summary", ""),
            "training_gaps": insights.get("trainingGaps", [])
        },
        "transcript": [],  # To be populated with diarized segments
        "metrics": {},
        "tags": analysis.get("transcript_tags", {})
    }
