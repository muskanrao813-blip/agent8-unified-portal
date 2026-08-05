from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.db.session import get_db
from app.schemas.dietician import DieticianTrendResponse, DieticianHistoryItem, DieticianResponse, DieticianListItem, DieticianSummaryResponse
from app.db import models
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def _generate_coaching_pointers(dimension_averages: dict) -> list[str]:
    """Generate actionable coaching pointers from lowest-scoring dimensions."""
    pointers = []
    sorted_dims = sorted(dimension_averages.items(), key=lambda x: x[1])

    for dim_name, score in sorted_dims[:3]:  # Top 3 weakest
        if dim_name == "discovery_assessment" and score < 7:
            pointers.append("Spend more time on patient history and lifestyle before presenting a plan")
        elif dim_name == "empathy_communication" and score < 7:
            pointers.append("Increase patient talking time — ask open-ended questions and listen actively")
        elif dim_name == "rushed_forced_detection" and score > 4:
            pointers.append("Consultation appears rushed — avoid giving diet plan in first 2 minutes")
        elif dim_name == "adherence_counselling" and score < 7:
            pointers.append("Discuss barriers to compliance and motivate the patient more explicitly")
        elif dim_name == "consultation_completeness" and score < 7:
            pointers.append("Ensure BMI, health goals, existing conditions, and follow-up date are all covered")

    return pointers[:3]  # Return top 3


@router.get("/dieticians/", response_model=list[DieticianListItem])
async def list_dieticians(db: Session = Depends(get_db)):
    """Get list of all dieticians with summary stats."""
    try:
        dieticians = db.query(models.Dietician).all()
        result = []

        for dietician in dieticians:
            call_count = db.query(func.count(models.Call.id)).filter(
                models.Call.dietician_id == dietician.id,
                models.Call.status == models.CallStatus.completed
            ).scalar() or 0

            avg_score = None
            if call_count > 0:
                avg_score = db.query(func.avg(models.RubricScore.overall_weighted_score)).filter(
                    models.RubricScore.call_id.in_(
                        db.query(models.Call.id).filter(
                            models.Call.dietician_id == dietician.id,
                            models.Call.status == models.CallStatus.completed
                        )
                    )
                ).scalar()

            result.append(DieticianListItem(
                id=dietician.id,
                name=dietician.name,
                external_id=dietician.external_id,
                call_count=call_count,
                avg_score=float(avg_score) if avg_score else None,
            ))

        return result
    except Exception as e:
        logger.error(f"Error listing dieticians: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dieticians/{dietician_id}/history", response_model=DieticianTrendResponse)
async def get_dietician_history(dietician_id: str, db: Session = Depends(get_db)):
    """Get dietician score trend over time (last 10 calls)."""
    try:
        import uuid
        try:
            dietician_uuid = uuid.UUID(dietician_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid dietician ID format")

        dietician = db.query(models.Dietician).filter(models.Dietician.id == dietician_uuid).first()
        if not dietician:
            raise HTTPException(status_code=404, detail="Dietician not found")

        calls = (
            db.query(models.Call)
            .filter(models.Call.dietician_id == dietician_uuid)
            .order_by(desc(models.Call.call_datetime))
            .limit(10)
            .all()
        )

        history_items = []
        total_score = 0
        for call in calls:
            rubric_score = (
                db.query(models.RubricScore)
                .filter(models.RubricScore.call_id == call.id)
                .first()
            )
            score = rubric_score.overall_weighted_score if rubric_score else None
            if score:
                total_score += score
            history_items.append(
                DieticianHistoryItem(
                    call_id=call.id,
                    call_datetime=call.call_datetime,
                    overall_weighted_score=score,
                    status=call.status,
                )
            )

        avg_score = total_score / len(calls) if calls else None

        return DieticianTrendResponse(
            dietician=DieticianResponse.from_orm(dietician),
            last_10_calls=history_items,
            average_score=avg_score,
            call_count=len(calls),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dietician history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dieticians/{dietician_id}/flags")
async def get_dietician_flags(dietician_id: str, db: Session = Depends(get_db)):
    """Get all QA flags for dietician (rolling 30-day/10-call window)."""
    try:
        import uuid
        try:
            dietician_uuid = uuid.UUID(dietician_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid dietician ID format")

        dietician = db.query(models.Dietician).filter(models.Dietician.id == dietician_uuid).first()
        if not dietician:
            raise HTTPException(status_code=404, detail="Dietician not found")

        calls = (
            db.query(models.Call)
            .filter(models.Call.dietician_id == dietician_uuid)
            .order_by(desc(models.Call.call_datetime))
            .limit(10)
            .all()
        )

        flags_by_type = {}
        for call in calls:
            qa_flags = db.query(models.QAFlag).filter(models.QAFlag.call_id == call.id).all()
            for flag in qa_flags:
                if flag.flag_type not in flags_by_type:
                    flags_by_type[flag.flag_type] = {"count": 0, "instances": []}
                if flag.triggered:
                    flags_by_type[flag.flag_type]["count"] += 1
                    flags_by_type[flag.flag_type]["instances"].append({
                        "call_id": str(call.id),
                        "call_datetime": call.call_datetime,
                        "detail": flag.detail,
                    })

        return {
            "dietician_id": str(dietician_id),
            "dietician_name": dietician.name,
            "flags": flags_by_type,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dietician flags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dieticians/{dietician_id}/summary", response_model=DieticianSummaryResponse)
async def get_dietician_summary(dietician_id: str, db: Session = Depends(get_db)):
    """Get comprehensive dietician summary with peer benchmarking and coaching pointers."""
    try:
        import uuid
        try:
            dietician_uuid = uuid.UUID(dietician_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid dietician ID format")

        dietician = db.query(models.Dietician).filter(models.Dietician.id == dietician_uuid).first()
        if not dietician:
            raise HTTPException(status_code=404, detail="Dietician not found")

        # Get last 30 completed calls (or fewer)
        calls = (
            db.query(models.Call)
            .filter(
                models.Call.dietician_id == dietician_uuid,
                models.Call.status == models.CallStatus.completed
            )
            .order_by(desc(models.Call.call_datetime))
            .limit(30)
            .all()
        )

        if not calls:
            raise HTTPException(status_code=404, detail="No completed calls for this dietician")

        # Compute dimension averages
        dimension_scores = {
            "discovery_assessment": [],
            "empathy_communication": [],
            "rushed_forced_detection": [],
            "adherence_counselling": [],
            "consultation_completeness": [],
        }

        avg_overall = 0
        flag_counts = {}
        trend_items = []
        retraining_recommended = False

        for call in calls:
            rubric_scores = db.query(models.RubricScore).filter(
                models.RubricScore.call_id == call.id
            ).all()

            for rs in rubric_scores:
                if rs.dimension in dimension_scores:
                    dimension_scores[rs.dimension].append(rs.score)
                if rs.overall_weighted_score:
                    avg_overall += rs.overall_weighted_score

            qa_flags = db.query(models.QAFlag).filter(models.QAFlag.call_id == call.id).all()
            for flag in qa_flags:
                if flag.triggered:
                    flag_counts[flag.flag_type] = flag_counts.get(flag.flag_type, 0) + 1

            feedback = db.query(models.FeedbackNote).filter(
                models.FeedbackNote.call_id == call.id
            ).first()
            if feedback and feedback.retraining_recommended:
                retraining_recommended = True

            if rubric_scores:
                trend_items.append(DieticianHistoryItem(
                    call_id=call.id,
                    call_datetime=call.call_datetime,
                    overall_weighted_score=rubric_scores[0].overall_weighted_score,
                    status=call.status.value,
                ))

        # Compute dimension averages
        dimension_averages = {}
        for dim, scores in dimension_scores.items():
            if scores:
                dimension_averages[dim] = round(sum(scores) / len(scores), 1)
            else:
                dimension_averages[dim] = 0.0

        total_calls = len(calls)
        avg_overall = round(avg_overall / total_calls, 1) if total_calls > 0 else 0.0

        # Peer benchmarking
        all_dieticians = db.query(models.Dietician).all()
        peer_scores = []

        for other_dietician in all_dieticians:
            other_calls = db.query(models.Call).filter(
                models.Call.dietician_id == other_dietician.id,
                models.Call.status == models.CallStatus.completed
            ).all()

            if other_calls:
                other_avg = db.query(func.avg(models.RubricScore.overall_weighted_score)).filter(
                    models.RubricScore.call_id.in_([c.id for c in other_calls])
                ).scalar() or 0
                peer_scores.append(float(other_avg) if other_avg else 0)

        team_avg_score = round(sum(peer_scores) / len(peer_scores), 1) if peer_scores else 0.0
        peer_scores_sorted = sorted(peer_scores, reverse=True)
        peer_rank = peer_scores_sorted.index(avg_overall) + 1 if avg_overall in peer_scores_sorted else len(peer_scores_sorted) + 1

        coaching_pointers = _generate_coaching_pointers(dimension_averages)

        return DieticianSummaryResponse(
            dietician_id=dietician.id,
            name=dietician.name,
            total_calls_analysed=total_calls,
            avg_overall_score=avg_overall,
            dimension_averages=dimension_averages,
            flag_counts=flag_counts,
            retraining_recommended=retraining_recommended,
            trend=trend_items,
            peer_rank=peer_rank,
            peer_total=len(all_dieticians),
            team_avg_score=team_avg_score,
            coaching_pointers=coaching_pointers,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dietician summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
