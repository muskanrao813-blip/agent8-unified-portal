from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.call import ValidationReport, CallDetailResponse
from app.services.ingestion import IngestService
from app.utils.template import generate_excel_template
from app.db import models
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/template")
async def download_template():
    """Download blank Excel template for call metadata."""
    try:
        template_bytes = generate_excel_template()
        return StreamingResponse(
            iter([template_bytes.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=dietician_calls_template.xlsx"},
        )
    except Exception as e:
        logger.error(f"Error generating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calls/bulk-upload", response_model=ValidationReport)
async def bulk_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload Excel file with call metadata for processing."""
    try:
        ingest = IngestService(db)
        validation_report = await ingest.validate_and_ingest_excel(file)
        return validation_report
    except Exception as e:
        logger.error(f"Error in bulk upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calls/upload-with-audio", response_model=ValidationReport)
async def upload_with_audio(
    excel_file: UploadFile = File(...),
    audio_files: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db)
):
    """
    Upload Excel file with call metadata + audio files.

    Excel must have 'recording_url' column with filenames (e.g., "call_001.wav").
    Audio files are matched by filename and processed via Whisper + Claude CLI.
    """
    try:
        ingest = IngestService(db)
        validation_report = await ingest.validate_and_ingest_excel_with_audio(
            excel_file, audio_files
        )
        return validation_report
    except Exception as e:
        logger.error(f"Error in audio upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calls/audio-upload")
async def audio_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a single audio file for transcription and QA analysis."""
    try:
        ingest = IngestService(db)
        result = await ingest.validate_and_ingest_audio(file)
        return result
    except Exception as e:
        logger.error(f"Error in audio upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calls", response_model=dict)
async def create_call(call_data: dict, db: Session = Depends(get_db)):
    """Create a single call record."""
    try:
        ingest = IngestService(db)
        call = await ingest.create_single_call(call_data)
        return {"id": str(call.id), "status": "queued"}
    except Exception as e:
        logger.error(f"Error creating call: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/calls", response_model=list)
async def list_calls(db: Session = Depends(get_db)):
    """List all completed calls with summary info."""
    try:
        calls = db.query(models.Call).filter(
            models.Call.status.in_(["completed", "processing", "pending"])
        ).order_by(models.Call.created_at.desc()).all()

        result = []
        for call in calls:
            metrics = db.query(models.CallMetrics).filter(models.CallMetrics.call_id == call.id).first()
            rubric_scores = db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).all()

            overall_score = None
            if rubric_scores:
                overall_score = rubric_scores[0].overall_weighted_score

            # Resolve patient name from Gemini entities if available
            transcript = db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first()
            gemini_patient = None
            _bad_names = {"not mentioned", "unknown", "unknown patient", "", "none", "not identified"}
            if transcript and transcript.raw_transcript_json:
                entities = transcript.raw_transcript_json.get("entities", {})
                name = entities.get("customer_name", "")
                if name and name.lower() not in _bad_names:
                    gemini_patient = name

            # Derive per-dimension scores for the list
            scores = {"greeting": 0, "empathy": 0, "compliance": 0, "technical": 0}
            for rs in rubric_scores:
                dim = rs.dimension
                if "greeting" in dim or "rapport" in dim:
                    scores["greeting"] = round(rs.score or 0)
                elif "empathy" in dim or "communication" in dim:
                    scores["empathy"] = round(rs.score or 0)
                elif "compliance" in dim or "sop" in dim or "adherence" in dim:
                    scores["compliance"] = round(rs.score or 0)
                elif "technical" in dim or "completeness" in dim or "action" in dim:
                    scores["technical"] = round(rs.score or 0)

            qa_flags_list = db.query(models.QAFlag).filter(models.QAFlag.call_id == call.id).all()
            call_date_str = call.call_datetime.strftime("%b %d, %Y") if call.call_datetime else ""
            qa_alerts = [
                {
                    "id": f.flag_type,
                    "title": f.flag_type.replace("_", " ").title(),
                    "description": f.detail or "",
                    "severity": "critical" if f.triggered else "info",
                    "status": "active" if f.triggered else "resolved",
                    "recordingId": str(call.id),
                    "recordingName": call.appointment_id or f"Call {str(call.id)[:8]}",
                    "dieticianName": call.dietician.name if call.dietician else "Unknown",
                    "patientName": call.patient_name or "Unknown",
                    "date": call_date_str,
                }
                for f in qa_flags_list if f.triggered
            ]

            result.append({
                "id": str(call.id),
                "dietician_name": call.dietician.name if call.dietician else "Unknown",
                "patient_name": gemini_patient or (call.patient_name if call.patient_name and call.patient_name.lower() not in {"unknown", "unknown patient", ""} else "Not Identified"),
                "appointment_id": call.appointment_id,
                "call_datetime": call.call_datetime,
                "call_duration_seconds": call.call_duration_seconds,
                "status": call.status,
                "overall_weighted_score": overall_score,
                "scores": scores,
                "qaAlerts": qa_alerts,
                "dietician_talk_ratio_pct": metrics.dietician_talk_ratio_pct if metrics else None,
            })

        return result
    except Exception as e:
        logger.error(f"Error listing calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/{call_id}", response_model=CallDetailResponse)
async def get_call(call_id: str, db: Session = Depends(get_db)):
    """Get full call result with transcript, scorecard, and flags."""
    try:
        import uuid
        try:
            call_uuid = uuid.UUID(call_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid call ID format")

        call = db.query(models.Call).filter(models.Call.id == call_uuid).first()
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")

        transcript = db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first()
        metrics = db.query(models.CallMetrics).filter(models.CallMetrics.call_id == call.id).first()
        rubric_scores = db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).all()
        qa_flags = db.query(models.QAFlag).filter(models.QAFlag.call_id == call.id).all()
        feedback = db.query(models.FeedbackNote).filter(models.FeedbackNote.call_id == call.id).first()

        overall_weighted_score = None
        if rubric_scores:
            overall_weighted_score = rubric_scores[0].overall_weighted_score

        feedback_bullets = []
        retraining_recommended = False
        if feedback:
            feedback_bullets = [b.strip() for b in feedback.bullet.split("|")]
            retraining_recommended = feedback.retraining_recommended

        # ── Transcript ──
        transcript_data = {}
        diarized_turns = []
        gemini_entities = {}
        if transcript and transcript.raw_transcript_json:
            raw_json = transcript.raw_transcript_json
            gemini_entities = raw_json.get("entities", {})
            full_text = raw_json.get("text", "")
            diarized_lines = raw_json.get("diarized_lines", transcript.diarized_segments or [])
            transcript_data = {
                "provider": transcript.provider,
                "text": full_text,
                "text_reconstructed": raw_json.get("text_reconstructed", full_text),
                "engine": raw_json.get("engine", "gemini"),
                "language": raw_json.get("language", ""),
                "audio_quality": raw_json.get("audio_quality", ""),
                "gemini_confidence": raw_json.get("gemini_confidence", ""),
                "entities": gemini_entities,
                "diarized_lines": diarized_lines,
                # Legacy compat keys
                "claude_reconstruction": {"text": raw_json.get("text_reconstructed", full_text)},
                "segments": diarized_lines,
            }
            diarized_turns = diarized_lines

        # ── Scores (from rubric_scores table) ──
        scores_dict = {"greeting": 0, "empathy": 0, "compliance": 0, "technical": 0}
        for rs in rubric_scores:
            dim = rs.dimension
            if "greeting" in dim or "rapport" in dim:
                scores_dict["greeting"] = round(rs.score or 0)
            elif "empathy" in dim or "communication" in dim:
                scores_dict["empathy"] = round(rs.score or 0)
            elif "compliance" in dim or "sop" in dim or "adherence" in dim:
                scores_dict["compliance"] = round(rs.score or 0)
            elif "technical" in dim or "completeness" in dim or "action" in dim:
                scores_dict["technical"] = round(rs.score or 0)

        # ── Insights (from rubric raw_llm_response or feedback bullets) ──
        insights = {"whatWentWell": [], "areasForImprovement": [], "summary": "", "trainingGapRecs": []}
        for rs in rubric_scores:
            raw = rs.raw_llm_response or {}
            if isinstance(raw, dict) and raw.get("insights"):
                ins = raw["insights"]
                insights["whatWentWell"] = ins.get("whatWentWell", [])
                insights["areasForImprovement"] = ins.get("areasForImprovement", [])
                insights["summary"] = ins.get("summary", "")
                insights["trainingGapRecs"] = ins.get("trainingGapRecs", [])
                break
        if not insights["summary"] and feedback_bullets:
            insights["summary"] = feedback_bullets[0] if feedback_bullets else ""

        # ── QA Flags → FE QAAlert shape ──
        dietician_name = call.dietician.name if call.dietician else "Unknown"
        call_name = call.appointment_id or f"Call {str(call.id)[:8]}"
        call_date = call.call_datetime.strftime("%b %d, %Y") if call.call_datetime else ""
        qa_alerts_fe = [
            {
                "id": f.flag_type,
                "title": f.flag_type.replace("_", " ").title(),
                "description": f.detail or "",
                "severity": "critical" if f.triggered else "info",
                "status": "active" if f.triggered else "resolved",
                "recordingId": str(call.id),
                "recordingName": call_name,
                "dieticianName": dietician_name,
                "patientName": call.patient_name or "Unknown",
                "date": call_date,
            }
            for f in qa_flags
        ]

        # ── Resolve patient name: prefer Gemini entity over Excel column ──
        raw_gemini_name = gemini_entities.get("customer_name", "")
        excel_name = call.patient_name or ""
        _invalid = {"not mentioned", "unknown", "unknown patient", "", "none", "not identified"}
        patient_name = (
            raw_gemini_name if raw_gemini_name and raw_gemini_name.lower() not in _invalid
            else excel_name if excel_name and excel_name.lower() not in _invalid
            else "Not Identified"
        )

        return {
            "id": call.id,
            "dietician_id": call.dietician_id,
            "patient_id": call.patient_id,
            "patient_name": patient_name,
            "appointment_id": call.appointment_id,
            "call_datetime": call.call_datetime,
            "recording_url": call.recording_url,
            "call_duration_seconds": call.call_duration_seconds,
            "status": call.status,
            "created_at": call.created_at,
            "processed_at": call.processed_at,
            "error_message": call.error_message,
            "transcript": transcript_data if transcript_data else {"segments": []},
            "metrics": {
                "duration_seconds": metrics.duration_seconds if metrics else None,
                "dietician_talk_ratio_pct": metrics.dietician_talk_ratio_pct if metrics else None,
                "patient_talk_ratio_pct": metrics.patient_talk_ratio_pct if metrics else None,
                "interruption_count": metrics.interruption_count if metrics else None,
                "avg_response_latency_seconds": metrics.avg_response_latency_seconds if metrics else None,
                "time_to_first_plan_mention_seconds": metrics.time_to_first_plan_mention_seconds if metrics else None,
                "silence_pct": metrics.silence_pct if metrics else None,
                "off_topic_time_pct": metrics.off_topic_time_pct if metrics else None,
            },
            "rubric_scores": [
                {
                    "dimension": rs.dimension,
                    "score": rs.score,
                    "evidence": rs.evidence,
                    "sub_criteria": rs.sub_criteria,
                }
                for rs in rubric_scores
            ],
            "scores": scores_dict,                  # greeting/empathy/compliance/technical
            "insights": insights,                   # whatWentWell/areasForImprovement/summary
            "qa_flags": [{"flag_type": f.flag_type, "triggered": f.triggered, "detail": f.detail} for f in qa_flags],
            "qaAlerts": qa_alerts_fe,               # FE-ready QAAlert shape
            "entities": gemini_entities,            # Gemini-extracted entities
            "raw_transcript": transcript_data.get("text", "") if transcript_data else "",
            "reconstructed_transcript": transcript_data.get("text_reconstructed", "") if transcript_data else "",
            "feedback_notes": {"bullets": feedback_bullets, "retraining_recommended": retraining_recommended},
            "overall_weighted_score": overall_weighted_score,
            "dietician_name": dietician_name,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/{call_id}/transcript")
async def get_transcript(call_id: str, db: Session = Depends(get_db)):
    """Get diarized transcript only."""
    try:
        import uuid
        try:
            call_uuid = uuid.UUID(call_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid call ID format")

        transcript = db.query(models.Transcript).filter(models.Transcript.call_id == call_uuid).first()
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")

        return {"segments": transcript.diarized_segments}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dieticians")
async def list_dieticians(db: Session = Depends(get_db)):
    """Get per-dietician performance report aggregated from completed calls."""
    try:
        dieticians = db.query(models.Dietician).all()
        result = []

        for dietician in dieticians:
            calls = db.query(models.Call).filter(
                models.Call.dietician_id == dietician.id,
                models.Call.status == "completed"
            ).all()

            if not calls:
                continue

            scores_all = []
            compliance_scores = []
            # alert_title -> set of call IDs where it appears
            alert_call_map: dict = {}
            training_gaps = []

            for call in calls:
                rubric_scores = db.query(models.RubricScore).filter(
                    models.RubricScore.call_id == call.id
                ).all()
                if rubric_scores:
                    overall = rubric_scores[0].overall_weighted_score or 0
                    scores_all.append(overall)
                    # compliance dimension score for SOP %
                    for rs in rubric_scores:
                        if rs.dimension == "compliance":
                            compliance_scores.append(rs.score or 0)
                            break

                # Aggregate triggered QA flags by title across calls
                flags = db.query(models.QAFlag).filter(
                    models.QAFlag.call_id == call.id,
                    models.QAFlag.triggered == True
                ).all()
                for flag in flags:
                    title = flag.flag_type
                    if title not in alert_call_map:
                        alert_call_map[title] = {
                            "call_ids": set(),
                            "detail": flag.detail or "",
                        }
                    alert_call_map[title]["call_ids"].add(str(call.id))

                # Pull training gaps from first rubric score's raw_llm_response
                seen_gap_titles = {g["title"] for g in training_gaps}
                for rs in rubric_scores:
                    raw = rs.raw_llm_response or {}
                    if isinstance(raw, dict):
                        gaps = raw.get("insights", {}).get("trainingGaps") or raw.get("insights", {}).get("trainingGapRecs", [])
                        for gap in gaps:
                            title = gap.get("title", "")
                            if not title or title in seen_gap_titles:
                                continue
                            seen_gap_titles.add(title)
                            training_gaps.append({
                                "id": title,  # stable, deduped by title
                                "title": title,
                                "description": gap.get("description", ""),
                                "category": gap.get("type", "compliance").replace("_", " ").title(),
                                "urgency": gap.get("urgency", "Mid-term"),
                                "assigned": False,
                                "type": gap.get("type", "compliance"),
                            })
                    break

            total_calls = len(calls)
            avg_score = round(sum(scores_all) / total_calls, 1) if scores_all else 0
            avg_compliance = round(sum(compliance_scores) / len(compliance_scores), 1) if compliance_scores else 0

            trend_vals = [round(s / 10, 1) for s in scores_all[-5:]] if scores_all else [5, 5, 5, 5, 5]
            while len(trend_vals) < 5:
                trend_vals.insert(0, trend_vals[0] if trend_vals else 5)

            trend_direction = (
                "up" if len(scores_all) > 1 and scores_all[-1] > scores_all[0]
                else "down" if len(scores_all) > 1 and scores_all[-1] < scores_all[0]
                else "flat"
            )
            ai_status = (
                "Exceeding Goals" if avg_score >= 80
                else "Training Required" if avg_score < 40
                else "Target Met"
            )

            # Build aggregated QA alerts: each unique title + how many calls it appeared in
            # Deduplicate alerts by grouping similar ones and keeping most important
            alert_groups = {
                "Missing Discovery": ["Missing Discovery"],
                "No Health Assessment First": ["Incomplete Health Assessment & Lack of Personalization", "Generic Communication Protocol"],
                "Generic Plan Delivered": ["Generic Diet Plan Delivery", "Generic Advice Protocol"],
                "Forced Consultation": ["Forced Consultation", "Incomplete Consultation/Early Termination"],
                "Poor Adherence Counselling": ["Poor Adherence Counselling"],
                "Poor Communication": ["Poor Call Structure and Professionalism", "Poor Communication Flow and Lack of Follow-up Plan", "Poor Professionalism and Confusion"],
                "Dismissive Clinical Approach": ["Dismissive Clinical Approach"],
            }

            # Aggregate by group: keep most frequent alert from each group
            deduped_alerts = {}
            for group_name, alert_titles in alert_groups.items():
                # Find the most frequent alert in this group
                best_alert = None
                best_count = 0
                for title in alert_titles:
                    if title in alert_call_map:
                        count = len(alert_call_map[title]["call_ids"])
                        if count > best_count:
                            best_count = count
                            best_alert = (title, alert_call_map[title], count)

                # Use group name if we found an alert, otherwise skip
                if best_alert:
                    title, info, call_count = best_alert
                    deduped_alerts[group_name] = {
                        "detail": info["detail"],
                        "call_count": call_count,
                        "original_title": title,  # Track original for context
                    }

            # Build final alert list with deduplication
            aggregated_alerts = []
            critical_alert_types = {
                "Missing Discovery",
                "No Health Assessment First",
                "Generic Plan Delivered",
                "Forced Consultation",
                "Poor Adherence Counselling",
                "Dismissive Clinical Approach",
            }

            for title, info in sorted(deduped_alerts.items(), key=lambda x: -x[1]["call_count"]):
                call_count = info["call_count"]

                # Determine severity: safety-critical issues are ALWAYS critical
                if title in critical_alert_types:
                    severity = "critical"
                elif call_count == total_calls:
                    severity = "critical"
                elif call_count > 1:
                    severity = "warning"
                else:
                    severity = "info"

                aggregated_alerts.append({
                    "id": title,
                    "title": title,
                    "description": info["detail"],
                    "callCount": call_count,
                    "totalCalls": total_calls,
                    "callFrequency": f"{call_count}/{total_calls} calls",
                    "severity": severity,
                    "original_alert": info["original_title"],  # Show what alert this represents
                })

            result.append({
                "dietician": {
                    "id": str(dietician.id),
                    "name": dietician.name,
                    "initials": "".join(w[0].upper() for w in dietician.name.split()[:2]),
                    "role": "Clinical Dietician",
                    "avgScore": avg_score,
                    "avgComplianceScore": avg_compliance,
                    "trend": f"+{avg_score:.0f}%" if trend_direction == "up" else f"{avg_score:.0f}%",
                    "trendDirection": trend_direction,
                    "trendValues": trend_vals,
                    "sopBreaches": len([a for a in aggregated_alerts if a["severity"] == "critical"]),
                    "totalAlertTypes": len(aggregated_alerts),
                    "aiStatus": ai_status,
                    "totalCalls": total_calls,
                },
                "qaAlerts": aggregated_alerts,
                "trainingGaps": training_gaps,
            })

        return result
    except Exception as e:
        logger.error(f"Error fetching dieticians: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batches/{batch_id}")
async def get_batch_status(batch_id: str, db: Session = Depends(get_db)):
    """Get batch upload status."""
    try:
        import uuid
        try:
            batch_uuid = uuid.UUID(batch_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid batch ID format")

        batch = db.query(models.UploadBatch).filter(models.UploadBatch.id == batch_uuid).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

        calls = db.query(models.Call).filter(models.Call.batch_id == batch_uuid).all()
        call_statuses = {}
        for call in calls:
            call_statuses[str(call.id)] = call.status

        return {
            "batch_id": str(batch.id),
            "uploaded_at": batch.uploaded_at,
            "total_rows": batch.total_rows,
            "valid_rows": batch.valid_rows,
            "invalid_rows": batch.invalid_rows,
            "call_statuses": call_statuses,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batches/{batch_id}/progress")
async def get_batch_progress(batch_id: str, db: Session = Depends(get_db)):
    """Get batch processing progress with live call status and detailed step info."""
    try:
        import uuid
        try:
            batch_uuid = uuid.UUID(batch_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid batch ID format")

        batch = db.query(models.UploadBatch).filter(models.UploadBatch.id == batch_uuid).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

        calls = db.query(models.Call).filter(models.Call.batch_id == batch_uuid).all()

        completed = 0
        failed = 0
        pending = 0
        processing = 0
        call_details = []

        for call in calls:
            if call.status == models.CallStatus.completed:
                completed += 1
                current_step = "Completed"
                step_number = 6
            elif call.status == models.CallStatus.failed:
                failed += 1
                current_step = f"Failed: {call.error_message}"
                step_number = 0
            elif call.status == models.CallStatus.processing:
                processing += 1
                # Determine step based on what data exists
                if db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first():
                    if db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).first():
                        current_step = "Analyzing with AI..."
                        step_number = 4
                    else:
                        current_step = "Extracting metrics..."
                        step_number = 3
                else:
                    current_step = "Transcribing audio..."
                    step_number = 2
            else:  # pending
                pending += 1
                current_step = "Waiting to start..."
                step_number = 1

            # Get overall score for completed calls
            overall_score = None
            if call.status == models.CallStatus.completed:
                rubric_scores = db.query(models.RubricScore).filter(
                    models.RubricScore.call_id == call.id
                ).first()
                if rubric_scores:
                    overall_score = rubric_scores.overall_weighted_score

            try:
                dietician_name = call.dietician.name if (call.dietician and hasattr(call.dietician, 'name')) else None
            except:
                dietician_name = None

            call_details.append({
                "id": str(call.id),
                "status": call.status.value,
                "dietician_name": dietician_name,
                "patient_name": call.patient_name,
                "appointment_id": call.appointment_id,
                "overall_score": overall_score,
                "current_step": current_step,
                "step_number": step_number,
                "error_message": call.error_message,
            })

        total = len(calls)
        pct_complete = int((completed / total * 100)) if total > 0 else 0

        return {
            "batch_id": str(batch.id),
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "processing": processing,
            "pct_complete": pct_complete,
            "status_text": f"{completed} completed, {processing} processing, {pending} pending, {failed} failed",
            "calls": call_details,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching batch progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))
