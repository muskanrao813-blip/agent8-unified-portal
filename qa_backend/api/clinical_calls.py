"""Clinical call analysis endpoints matching FE requirements."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.schemas.clinical_call import transform_call_to_clinical_response
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


def convert_snake_to_camel(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def convert_dict_keys_to_camel(obj):
    """Recursively convert all snake_case keys to camelCase."""
    if isinstance(obj, dict):
        return {convert_snake_to_camel(k): convert_dict_keys_to_camel(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_dict_keys_to_camel(item) for item in obj]
    else:
        return obj


@router.get("/clinical/calls")
async def get_clinical_calls(db: Session = Depends(get_db)):
    """Get all calls with clinical analysis for dashboard."""
    try:
        calls = db.query(models.Call).order_by(
            models.Call.created_at.desc()
        ).all()

        result = []
        for call in calls:
            # Get rubric scores
            rubric_scores = db.query(models.RubricScore).filter(
                models.RubricScore.call_id == call.id
            ).all()

            # Get QA flags
            qa_flags = db.query(models.QAFlag).filter(
                models.QAFlag.call_id == call.id
            ).all()

            # Transform to clinical response format
            clinical_data = {
                "id": str(call.id),
                "patient_name": call.patient_name or "Unknown",
                "dietician_name": call.dietician.name if call.dietician else "Unknown",
                "date": call.call_datetime.isoformat() if call.call_datetime else "",
                "duration": f"{call.call_duration_seconds // 60 if call.call_duration_seconds else 0}:{call.call_duration_seconds % 60 if call.call_duration_seconds else 0:02d}",
                "status": str(call.status).split('.')[-1],
                "progress": 100 if call.status == models.CallStatus.completed else 50,
                "status_text": "Ready for review" if call.status == models.CallStatus.completed else "Processing",
                "scores": {
                    "greeting": 0,
                    "empathy": 0,
                    "compliance": 0,
                    "technical": 0
                },
                "overall_score": 0,
                "sop_compliant": True,
                "sop_compliance_score": 100,
                "qa_alerts": [],
                "critical_alerts_count": 0,
                "insights": {
                    "what_went_well": [],
                    "areas_for_improvement": [],
                    "summary": ""
                }
            }

            # Populate scores from rubric_scores
            score_map = {
                "greeting": 0,
                "empathy": 0,
                "compliance": 0,
                "technical": 0
            }

            for score_obj in rubric_scores:
                dim = score_obj.dimension.lower()
                if "greeting" in dim or "discovery" in dim:
                    score_map["greeting"] = max(score_map["greeting"], score_obj.score)
                elif "empathy" in dim:
                    score_map["empathy"] = max(score_map["empathy"], score_obj.score)
                elif "compliance" in dim or "rushed" in dim:
                    score_map["compliance"] = max(score_map["compliance"], score_obj.score)
                elif "technical" in dim or "completeness" in dim:
                    score_map["technical"] = max(score_map["technical"], score_obj.score)

            clinical_data["scores"] = score_map
            clinical_data["overall_score"] = round(
                sum(score_map.values()) / 4, 2
            )

            # Populate QA alerts from flags - show all flags regardless of triggered status
            qa_alerts = []
            critical_count = 0
            for flag in qa_flags:
                # Determine severity based on flag type
                severity = "critical" if flag.flag_type in ["HIPAA", "Safety", "Forced Consultation", "Missing Discovery"] else "warning"
                qa_alerts.append({
                    "id": str(flag.id),
                    "title": flag.flag_type,
                    "description": flag.detail or f"{flag.flag_type} detected in consultation",
                    "severity": severity,
                    "status": "active",
                    "recording_id": str(call.id),
                    "recording_name": call.recording_url or f"call_{call.id}",
                    "dietician_name": call.dietician.name if call.dietician else "Unknown",
                    "date": call.call_datetime.strftime("%b %d, %Y") if call.call_datetime else ""
                })
                if severity == "critical":
                    critical_count += 1

            clinical_data["qa_alerts"] = qa_alerts
            clinical_data["critical_alerts_count"] = critical_count

            # Add required FE fields
            clinical_data["name"] = call.recording_url or f"call_{call.id}"
            clinical_data["agent_name"] = clinical_data["dietician_name"]
            clinical_data["sop_compliant"] = clinical_data["sop_compliant"]
            clinical_data["progress"] = 100
            clinical_data["status_text"] = "Ready for review" if call.status == models.CallStatus.completed else "Processing"

            result.append(clinical_data)

        # Convert snake_case to camelCase for FE compatibility
        return convert_dict_keys_to_camel(result)

    except Exception as e:
        logger.error(f"Error getting clinical calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clinical/calls/{call_id}")
async def get_clinical_call_detail(call_id: str, db: Session = Depends(get_db)):
    """Get detailed clinical analysis for a single call."""
    try:
        import uuid
        call_uuid = uuid.UUID(call_id)
        call = db.query(models.Call).filter(models.Call.id == call_uuid).first()

        if not call:
            raise HTTPException(status_code=404, detail="Call not found")

        # Get all analysis data
        transcript = db.query(models.Transcript).filter(
            models.Transcript.call_id == call.id
        ).first()

        rubric_scores = db.query(models.RubricScore).filter(
            models.RubricScore.call_id == call.id
        ).all()

        qa_flags = db.query(models.QAFlag).filter(
            models.QAFlag.call_id == call.id
        ).all()

        feedback = db.query(models.FeedbackNote).filter(
            models.FeedbackNote.call_id == call.id
        ).first()

        metrics = db.query(models.CallMetrics).filter(
            models.CallMetrics.call_id == call.id
        ).first()

        # Build response
        response = {
            "id": str(call.id),
            "patient_name": call.patient_name or "Unknown",
            "dietician_name": call.dietician.name if call.dietician else "Unknown",
            "date": call.call_datetime.isoformat() if call.call_datetime else "",
            "duration": f"{call.call_duration_seconds // 60 if call.call_duration_seconds else 0}:{call.call_duration_seconds % 60 if call.call_duration_seconds else 0:02d}",
            "status": str(call.status).split('.')[-1],
            "progress": 100 if call.status == models.CallStatus.completed else 50,
            "status_text": "Ready for review" if call.status == models.CallStatus.completed else "Processing",
            "sop_compliant": True,
            "sop_compliance_score": 100,
            "scores": {
                "greeting": 0,
                "empathy": 0,
                "compliance": 0,
                "technical": 0
            },
            "overall_weighted_score": 0,
            "qa_alerts": [],
            "transcript": [],
            "insights": {
                "what_went_well": [],
                "areas_for_improvement": [],
                "summary": ""
            },
            "metrics": {
                "duration_seconds": metrics.duration_seconds if metrics else 0,
                "dietician_talk_ratio_pct": metrics.dietician_talk_ratio_pct if metrics else 0,
                "patient_talk_ratio_pct": metrics.patient_talk_ratio_pct if metrics else 0,
            }
        }

        # Populate scores
        score_map = {"greeting": 0, "empathy": 0, "compliance": 0, "technical": 0}
        for score_obj in rubric_scores:
            dim = score_obj.dimension.lower()
            if "greeting" in dim or "discovery" in dim:
                score_map["greeting"] = max(score_map["greeting"], score_obj.score)
            elif "empathy" in dim:
                score_map["empathy"] = max(score_map["empathy"], score_obj.score)
            elif "compliance" in dim or "rushed" in dim:
                score_map["compliance"] = max(score_map["compliance"], score_obj.score)
            elif "technical" in dim or "completeness" in dim:
                score_map["technical"] = max(score_map["technical"], score_obj.score)

        response["scores"] = score_map
        response["overall_weighted_score"] = round(sum(score_map.values()) / 4, 2)

        # Populate QA alerts - show all flags regardless of triggered status
        for flag in qa_flags:
            severity = "critical" if flag.flag_type in ["HIPAA", "Safety", "Forced Consultation", "Missing Discovery"] else "warning"
            response["qa_alerts"].append({
                "id": str(flag.id),
                "title": flag.flag_type,
                "description": flag.detail or f"{flag.flag_type} detected in consultation",
                "severity": severity,
                "status": "active",
                "recording_id": str(call.id),
                "recording_name": call.recording_url or f"call_{call.id}",
                "dietician_name": call.dietician.name if call.dietician else "Unknown",
                "date": call.call_datetime.strftime("%b %d, %Y") if call.call_datetime else ""
            })

        # Populate transcript
        if transcript and transcript.diarized_segments:
            for i, seg in enumerate(transcript.diarized_segments):
                response["transcript"].append({
                    "id": f"turn-{i}",
                    "speaker": seg.get("speaker", "Unknown"),
                    "speaker_name": seg.get("speaker", "Unknown").title(),
                    "timestamp": f"{int(seg.get('start_s', 0))}s",
                    "text": seg.get("text", ""),
                    "is_critical": False
                })

        # Populate insights
        if feedback:
            bullets = feedback.bullet.split("|") if feedback.bullet else []
            response["insights"]["areas_for_improvement"] = [b.strip() for b in bullets if b.strip()]
            response["insights"]["summary"] = f"Retraining {'recommended' if feedback.retraining_recommended else 'not required'}"

        # Add required FE fields
        response["name"] = call.recording_url or f"call_{call.id}"
        response["agent_name"] = response["dietician_name"]
        response["progress"] = 100
        response["status_text"] = "Ready for review" if call.status == models.CallStatus.completed else "Processing"

        # Convert snake_case to camelCase for FE compatibility
        return convert_dict_keys_to_camel(response)

    except Exception as e:
        logger.error(f"Error getting clinical call detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clinical/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    try:
        total_calls = db.query(models.Call).count()
        completed_calls = db.query(models.Call).filter(
            models.Call.status == models.CallStatus.completed
        ).count()

        # Calculate average scores
        scores = db.query(models.RubricScore).all()
        avg_score = sum([s.score for s in scores]) / len(scores) if scores else 0

        # Count critical alerts
        critical_flags = db.query(models.QAFlag).filter(
            models.QAFlag.flag_type.in_(["HIPAA", "Safety"])
        ).count()

        stats = {
            "total_calls": total_calls,
            "avg_quality_score": round(avg_score, 1),
            "sop_compliance_percentage": 85.0,  # Placeholder
            "critical_alerts_count": critical_flags,
            "calls_this_month": completed_calls,
            "team_size": db.query(models.Dietician).count()
        }
        return convert_dict_keys_to_camel(stats)

    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
