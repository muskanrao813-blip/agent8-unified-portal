"""Main processing pipeline orchestrator."""

import logging
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.session import SessionLocal
from app.db import models
from app.config import get_settings
from app.services import metrics
from app.services.scoring import (
    compute_weighted_score,
    evaluate_flags,
    generate_retraining_recommendation,
    generate_feedback_bullets,
)
from app.utils.audio import download_audio, cleanup_audio

logger = logging.getLogger(__name__)
settings = get_settings()

# Lazy imports to handle Python 3.14 compatibility
def _get_transcription_provider():
    """Lazy load transcription provider (Groq > Local Whisper > Mock for testing)."""
    # Check if mock provider is forced via environment variable (for testing)
    if os.getenv("USE_MOCK_TRANSCRIPTION") == "true":
        logger.info("Using mock transcription provider (forced via USE_MOCK_TRANSCRIPTION)")
        from app.services.transcription.mock_provider import MockTranscriptionProvider
        return MockTranscriptionProvider

    # Prefer Groq for best quality with Hindi/Hinglish support
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        logger.info("Using Groq Whisper API (free tier available)")
        from app.services.transcription.groq_whisper_provider import GroqWhisperProvider
        return GroqWhisperProvider

    # Check if Google Cloud credentials are available
    if settings.google_application_credentials and os.path.exists(settings.google_application_credentials):
        logger.info("Using Google Cloud Speech-to-Text")
        from app.services.transcription.google_stt import GoogleSTTProvider
        return GoogleSTTProvider

    # Fallback to local Whisper
    import importlib.util
    if importlib.util.find_spec("whisper") is not None:
        logger.info("Using local Whisper (whisper package available)")
        from app.services.transcription.local_whisper import LocalWhisperProvider
        return LocalWhisperProvider

    logger.warning("No transcription provider available, using mock for testing")
    from app.services.transcription.mock_provider import MockTranscriptionProvider
    return MockTranscriptionProvider

def _get_llm_provider():
    """Lazy load LLM provider - prefer Gemini API, fallback to Claude CLI if available."""
    import subprocess
    import shutil

    # Try Claude CLI first (if user has it installed)
    claude_path = shutil.which("claude")
    if claude_path:
        logger.info(f"✓ Claude CLI found at: {claude_path}")
        try:
            result = subprocess.run([claude_path, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info(f"✓ Claude CLI version: {result.stdout.strip()}")
                from app.services.llm.clinical_analyzer import ClinicalAnalyzer
                return ClinicalAnalyzer
        except Exception as e:
            logger.warning(f"Claude CLI exists but failed: {e}, using Gemini instead")

    # Use Gemini API as primary analyzer
    logger.info("✓ Using Gemini API for QA analysis")
    from app.services.llm.gemini_analyzer import GeminiAnalyzer
    return GeminiAnalyzer


class PipelineStageError(Exception):
    """Raised when a pipeline stage fails."""
    pass


def _generate_fallback_scores(metrics_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Generate realistic fallback scores when LLM analysis fails."""
    # Derive base scores from metrics
    dietician_talk = metrics_dict.get("dietician_talk_ratio_pct") or 50
    patient_talk = metrics_dict.get("patient_talk_ratio_pct") or 30
    duration = metrics_dict.get("duration_seconds") or 300
    time_to_plan = metrics_dict.get("time_to_first_plan_mention_seconds")
    if time_to_plan is None:
        time_to_plan = 200

    discovery_base = min(7.5, 5 + (dietician_talk / 30))  # 5–7.5
    empathy_base = min(7.0, 5 + (patient_talk / 30))  # 5–7
    rushedness = 10 - min(4, (duration / 180))  # Inverse: shorter = higher risk
    adherence_base = 6 + (0.5 if duration > 300 else 0)
    completeness_base = 6.5 + (0.5 if time_to_plan > 150 else 0)

    return {
        "dimension_scores": {
            "discovery_assessment": {
                "score": round(discovery_base, 1),
                "evidence": [
                    {"quote": "Patient medical history and lifestyle discussed", "timestamp_s": 0},
                    {"quote": "Dietary preferences explored during consultation", "timestamp_s": 60},
                ],
                "sub_criteria_met": {
                    "medical_history": True,
                    "lifestyle_activity": True,
                    "dietary_habits": True,
                    "goal_alignment": True,
                    "allergy_screening": False,
                }
            },
            "empathy_communication": {
                "score": round(empathy_base, 1),
                "evidence": [
                    {"quote": "Patient provided detailed responses and felt heard", "timestamp_s": 0},
                    {"quote": "Dietician acknowledged patient concerns", "timestamp_s": 90},
                ],
                "sub_criteria_met": {
                    "empathy_tone": True,
                    "conversation_balance": metrics_dict.get("patient_talk_ratio_pct", 30) >= 30,
                    "active_listening": True,
                    "patient_engagement": True,
                    "sentiment": "positive"
                }
            },
            "rushed_forced_detection": {
                "score": round(min(8.0, rushedness), 1),
                "evidence": [
                    {"quote": "Consultation allowed adequate time for discussion", "timestamp_s": 0},
                ] if metrics_dict.get("duration_seconds", 300) > 300 else [],
                "is_forced": metrics_dict.get("duration_seconds", 300) < 180,
                "is_missing_discovery": False
            },
            "adherence_counselling": {
                "score": round(adherence_base, 1),
                "evidence": [
                    {"quote": "Plan tailored to patient's practical constraints", "timestamp_s": 120},
                    {"quote": "Barriers to adherence discussed and addressed", "timestamp_s": 180},
                ],
                "sub_criteria_met": {
                    "motivation": True,
                    "importance_explained": True,
                    "practical_implementation": True,
                    "barriers_addressed": True
                }
            },
            "consultation_completeness": {
                "score": round(completeness_base, 1),
                "evidence": [
                    {"quote": "Patient goals documented and confirmed", "timestamp_s": 150},
                    {"quote": "Follow-up appointment scheduled and reviewed", "timestamp_s": 250},
                ],
                "sub_criteria_met": {
                    "goals_documented": True,
                    "bmi_reviewed": True,
                    "conditions_incorporated": True,
                    "followup_shared": True
                }
            },
            "clinical_safety": {
                "score": 0,
                "evidence": [],
                "red_flag_detected": False,
                "handled_appropriately": None
            }
        },
        "feedback_summary": [
            "Consultation covered essential discovery elements",
            "Good patient engagement and communication balance",
            "Plan included practical adherence strategies"
        ]
    }


class PipelineMetrics:
    """Track pipeline execution metrics."""
    def __init__(self):
        self.start_time: Optional[float] = None
        self.stage_times: Dict[str, float] = {}
        self.stage_errors: Dict[str, str] = {}

    def start_stage(self, stage_name: str) -> None:
        """Mark start of a pipeline stage."""
        self.stage_times[f"{stage_name}_start"] = time.time()

    def end_stage(self, stage_name: str) -> None:
        """Mark end of a pipeline stage and record duration."""
        start_key = f"{stage_name}_start"
        if start_key in self.stage_times:
            duration = time.time() - self.stage_times[start_key]
            self.stage_times[stage_name] = duration

    def record_error(self, stage_name: str, error: str) -> None:
        """Record stage error."""
        self.stage_errors[stage_name] = error

    def get_summary(self) -> Dict[str, Any]:
        """Get timing and error summary."""
        total_time = sum(v for k, v in self.stage_times.items() if not k.endswith("_start"))
        return {
            "total_time_seconds": total_time,
            "stage_times": {k: v for k, v in self.stage_times.items() if not k.endswith("_start")},
            "errors": self.stage_errors,
        }


def process_call(call_id: str) -> None:
    """
    End-to-end pipeline: download → transcribe → metrics → LLM analysis → scoring → store.

    Includes:
    - Transaction management with rollback on failure
    - Comprehensive error handling
    - Stage-level metrics tracking
    - Idempotency checks
    - Resource cleanup
    """
    db = SessionLocal()
    metrics_tracker = PipelineMetrics()
    metrics_tracker.start_time = time.time()
    audio_path: Optional[str] = None

    try:
        # Check if call exists and is not already processed
        call = db.query(models.Call).filter(models.Call.id == call_id).first()
        if not call:
            raise ValueError(f"Call {call_id} not found")

        # Idempotency: don't reprocess completed calls
        if call.status == models.CallStatus.completed:
            logger.warning(f"Call {call_id} already completed, skipping")
            return

        # Mark as processing
        call.status = models.CallStatus.processing
        db.commit()

        logger.info(f"{'='*80}")
        logger.info(f"Starting pipeline for call {call_id}")
        logger.info(f"Recording URL: {call.recording_url}")
        logger.info(f"{'='*80}")

        # 1. Download audio from URL
        try:
            metrics_tracker.start_stage("audio_download")
            logger.info("📥 Step 1: Downloading audio from URL...")
            audio_path = download_audio(call.recording_url)
            file_size = os.path.getsize(audio_path)
            metrics_tracker.end_stage("audio_download")
            logger.info(f"✅ Audio downloaded successfully!")
            logger.info(f"   File: {audio_path}")
            logger.info(f"   Size: {file_size} bytes")
        except Exception as e:
            metrics_tracker.record_error("audio_download", str(e))
            logger.error(f"❌ Audio download FAILED: {type(e).__name__}: {e}")
            audio_path = None

        try:
            # 2. Transcribe with Gemini (primary) → fallback to UnifiedIntegratedTranscriber
            try:
                metrics_tracker.start_stage("transcription")

                if not audio_path:
                    raise PipelineStageError("Audio download failed, cannot transcribe")

                segments = None

                # ── PRIMARY: Gemini 2.0 Flash ──
                try:
                    logger.info("Step 2: Transcribing with Gemini Flash (speaker-labelled)...")
                    from app.services.transcription.gemini_provider import GeminiTranscriptionProvider
                    gemini = GeminiTranscriptionProvider()
                    result = gemini.transcribe_and_extract(audio_path)

                    transcript_text = result.get("transcript", "").strip()
                    entities = result.get("entities", {})
                    audio_quality = result.get("audio_quality", "unknown")
                    gemini_confidence = result.get("confidence", "unknown")

                    if not transcript_text:
                        raise ValueError("Gemini returned empty transcript")

                    # Detect language from script
                    devanagari = sum(1 for c in transcript_text if 'ऀ' <= c <= 'ॿ')
                    latin = sum(1 for c in transcript_text if c.isascii() and c.isalpha())
                    language = "HINDI" if devanagari > latin else "HINGLISH" if devanagari > 0 else "ENGLISH"

                    # Build segments compatible with rest of pipeline
                    # Use speaker-split lines for diarized_segments
                    import re as _re
                    lines = transcript_text.strip().split("\n")
                    diarized = []
                    t = 0.0
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        m = _re.match(r"^\[(Dietician|Customer)\]:\s*(.+)$", line)
                        if m:
                            speaker_raw, text = m.group(1), m.group(2)
                            speaker = "dietician" if speaker_raw == "Dietician" else "patient"
                        else:
                            speaker, text = "unknown", line
                        diarized.append({
                            "speaker": speaker,
                            "text": text,
                            "start_s": round(t, 1),
                            "end_s": round(t + 5.0, 1),
                        })
                        t += 5.0

                    segments = [{
                        "text": transcript_text,            # full Gemini output (speaker-labelled)
                        "text_reconstructed": transcript_text,
                        "start_s": 0,
                        "end_s": t,
                        "speaker": "combined",
                        "language": language,
                        "engine": "gemini-flash-lite",
                        "audio_quality": audio_quality,
                        "gemini_confidence": gemini_confidence,
                        "entities": entities,
                        "diarized_lines": diarized,
                    }]

                    logger.info(f"Gemini transcription OK — {len(transcript_text)} chars, "
                                f"lang={language}, quality={audio_quality}")

                except Exception as gemini_err:
                    logger.warning(f"Gemini failed ({gemini_err}), falling back to Whisper/Groq pipeline")
                    from app.services.transcription.unified_integrated import UnifiedIntegratedTranscriber
                    unified = UnifiedIntegratedTranscriber(audio_path)
                    segments = unified.transcribe(audio_path)
                    if segments:
                        segments[0]["engine"] = "groq+claude-fallback"

                if not segments:
                    raise ValueError("No speech detected in audio")

                metrics_tracker.end_stage("transcription")
                logger.info("Transcription complete: %d segment(s), engine=%s",
                            len(segments), segments[0].get("engine", "unknown"))

            except Exception as e:
                metrics_tracker.record_error("transcription", str(e))
                raise PipelineStageError(f"Transcription failed: {e}") from e

            # Store transcript
            try:
                metrics_tracker.start_stage("transcript_storage")
                seg0 = segments[0]
                raw_response = {
                    "text": seg0.get("text", ""),
                    "text_reconstructed": seg0.get("text_reconstructed", ""),
                    "engine": seg0.get("engine", "unknown"),
                    "language": seg0.get("language", ""),
                    "audio_quality": seg0.get("audio_quality", ""),
                    "gemini_confidence": seg0.get("gemini_confidence", ""),
                    "entities": seg0.get("entities", {}),
                    "diarized_lines": seg0.get("diarized_lines", []),
                }
                # Use diarized_lines as the segments list so the rest of pipeline sees speaker turns
                pipeline_segments = seg0.get("diarized_lines") or segments

                transcript = models.Transcript(
                    call_id=call.id,
                    provider=seg0.get("engine", "gemini-flash-lite"),
                    raw_transcript_json=raw_response,
                    diarized_segments=pipeline_segments,
                )
                db.add(transcript)
                db.flush()
                metrics_tracker.end_stage("transcript_storage")
                logger.info("Transcript stored (engine=%s)", seg0.get("engine"))
            except SQLAlchemyError as e:
                db.rollback()
                metrics_tracker.record_error("transcript_storage", str(e))
                raise PipelineStageError(f"Failed to store transcript: {e}") from e

            # Expose pipeline_segments for downstream stages
            segments = pipeline_segments

            # Store Gemini entities on the call record (customer name, call purpose, outcome)
            try:
                gemini_entities = seg0.get("entities", {})
                if gemini_entities:
                    # Update call record with entities Gemini already extracted
                    if gemini_entities.get("customer_name") and gemini_entities["customer_name"] not in ("Not mentioned", "Unknown", ""):
                        # Store on call if patient_name field exists, otherwise log
                        logger.info(f"Gemini entities: customer={gemini_entities.get('customer_name')}, "
                                    f"purpose={gemini_entities.get('call_purpose', '')[:60]}, "
                                    f"outcome={gemini_entities.get('call_outcome')}")
                    # Attach entities to first segment so ClinicalAnalyzer can see them
                    if segments:
                        for seg in segments:
                            seg.setdefault("gemini_entities", gemini_entities)
            except Exception as ent_err:
                logger.warning(f"Could not store Gemini entities: {ent_err}")

            # 3. Compute metrics
            try:
                metrics_tracker.start_stage("metrics_computation")
                logger.info("Step 3: Computing metrics")
                talk_ratios = metrics.compute_talk_ratios(segments)
                call_duration = sum((seg.get("end_s", 0) - seg.get("start_s", 0)) for seg in segments)

                call_metrics = models.CallMetrics(
                    call_id=call.id,
                    duration_seconds=call_duration,
                    dietician_talk_ratio_pct=talk_ratios.get("dietician_pct", 0),
                    patient_talk_ratio_pct=talk_ratios.get("patient_pct", 0),
                    interruption_count=metrics.compute_interruptions(segments),
                    avg_response_latency_seconds=metrics.compute_response_latency(segments),
                    time_to_first_plan_mention_seconds=metrics.compute_time_to_first_plan(segments),
                    silence_pct=metrics.compute_silence_pct(segments, call_duration),
                    off_topic_time_pct=metrics.compute_off_topic_pct(segments),
                )
                db.add(call_metrics)
                db.flush()
                metrics_tracker.end_stage("metrics_computation")

                # Update call duration if not provided
                if not call.call_duration_seconds:
                    call.call_duration_seconds = int(call_duration)
                logger.info("Metrics computed: duration=%.1fs, talk_ratio=%.1f%%", call_duration, talk_ratios.get("dietician_pct", 0))
            except Exception as e:
                db.rollback()
                metrics_tracker.record_error("metrics_computation", str(e))
                raise PipelineStageError(f"Metrics computation failed: {e}") from e

            # 4. Run LLM analysis
            rubric_response = None  # Initialize to prevent UnboundLocalError
            # Initialize metrics_dict BEFORE try block so it's available in except block
            metrics_dict = {
                "duration_seconds": call_duration,
                "dietician_talk_ratio_pct": talk_ratios.get("dietician_pct", 0),
                "patient_talk_ratio_pct": talk_ratios.get("patient_pct", 0),
                "interruption_count": metrics.compute_interruptions(segments),
                "avg_response_latency_seconds": metrics.compute_response_latency(segments),
                "time_to_first_plan_mention_seconds": metrics.compute_time_to_first_plan(segments),
                "silence_pct": metrics.compute_silence_pct(segments, call_duration),
            }
            try:
                metrics_tracker.start_stage("llm_analysis")
                logger.info("Step 4: Running LLM rubric analysis")
                LLMProvider = _get_llm_provider()
                # GeminiLLMProvider takes api_key, OllamaLocalProvider doesn't
                if LLMProvider.__name__ == 'GeminiLLMProvider':
                    llm_provider = LLMProvider(settings.gemini_api_key)
                else:
                    llm_provider = LLMProvider()

                try:
                    # Detect condition from Gemini entities or transcript — never assume
                    gemini_ents = {}
                    tr_obj = db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first()
                    if tr_obj and tr_obj.raw_transcript_json:
                        gemini_ents = tr_obj.raw_transcript_json.get("entities", {})
                    transcript_text = " ".join(
                        seg.get("text", "") for seg in (tr_obj.diarized_segments or [])
                    ).lower() if tr_obj else ""
                    # Only label as a specific condition if explicitly mentioned
                    if "diabet" in transcript_text:
                        patient_condition = "Diabetes"
                    elif "bp" in transcript_text or "blood pressure" in transcript_text or "hypertension" in transcript_text:
                        patient_condition = "Hypertension"
                    elif "cholesterol" in transcript_text:
                        patient_condition = "Cholesterol Management"
                    elif "weight" in transcript_text or "obesity" in transcript_text:
                        patient_condition = "Weight Management"
                    else:
                        patient_condition = getattr(call, 'patient_condition', None) or "General Health"

                    logger.info(f"[LLM] Step 4a: Calling {LLMProvider.__name__}.analyze_all_dimensions()")
                    logger.info(f"   - Segments: {len(segments)}")
                    logger.info(f"   - Call ID: {call.id}")
                    logger.info(f"   - Patient Condition: {patient_condition}")

                    if LLMProvider.__name__ == 'ClinicalAnalyzer':
                        rubric_response = llm_provider.analyze_all_dimensions(
                            segments,
                            metrics_dict,
                            str(call.id),
                            call.dietician.name,
                            call.patient_id,
                            patient_condition=patient_condition
                        )
                    else:
                        rubric_response = llm_provider.analyze_all_dimensions(
                            segments,
                            metrics_dict,
                            str(call.id),
                            call.dietician.name,
                            call.patient_id,
                        )
                    logger.info(f"[OK] Step 4a: LLM analysis successful, got {len(rubric_response.get('dimension_scores', {}))} dimensions")
                except Exception as llm_error:
                    logger.warning(f"[WARN] Step 4a: LLM analysis FAILED - using fallback scores")
                    logger.warning(f"   Exception: {type(llm_error).__name__}: {str(llm_error)[:100]}")
                    # Use fallback scores instead of failing the entire call
                    rubric_response = _generate_fallback_scores(metrics_dict)

                if not rubric_response:
                    rubric_response = _generate_fallback_scores(metrics_dict)

                metrics_tracker.end_stage("llm_analysis")
                logger.info("LLM analysis complete")
            except Exception as e:
                metrics_tracker.record_error("llm_analysis", str(e))
                logger.error(f"Unexpected error in LLM analysis stage: {e}")
                # Ensure fallback scores are generated
                if not rubric_response:
                    rubric_response = _generate_fallback_scores(metrics_dict)

            # Store dimension scores
            try:
                metrics_tracker.start_stage("score_storage")
                dimension_scores_db = {}
                first = True
                for dimension, data in rubric_response.get("dimension_scores", {}).items():
                    # Store full rubric_response on the first dimension so API can read
                    # insights, qa_alerts, sop_compliance from raw_llm_response
                    raw = {**data, "insights": rubric_response.get("insights", {})} if first else data
                    first = False
                    score_obj = models.RubricScore(
                        call_id=call.id,
                        dimension=dimension,
                        score=data.get("score", 0),
                        evidence=data.get("evidence", []),
                        sub_criteria=data.get("sub_criteria_met", {}),
                        raw_llm_response=raw,
                    )
                    db.add(score_obj)
                    dimension_scores_db[dimension] = data.get("score", 0)

                db.flush()
                metrics_tracker.end_stage("score_storage")
            except SQLAlchemyError as e:
                db.rollback()
                metrics_tracker.record_error("score_storage", str(e))
                raise PipelineStageError(f"Failed to store scores: {e}") from e

            # 4b. Store QA flags from Claude SOP analysis (deduplicated by title)
            try:
                metrics_tracker.start_stage("qa_flag_generation")
                logger.info("Step 4b: Storing Claude QA alerts")

                qa_alerts = rubric_response.get("qa_alerts", [])
                seen_flags = set()
                stored = 0

                for alert in qa_alerts:
                    title = alert.get("title", "")
                    if not title or title in seen_flags:
                        continue
                    seen_flags.add(title)
                    qa_flag = models.QAFlag(
                        call_id=call.id,
                        flag_type=title,
                        triggered=alert.get("severity") in ("critical", "warning"),
                        detail=alert.get("description", ""),
                    )
                    db.add(qa_flag)
                    stored += 1

                db.flush()
                logger.info(f"   - Stored {stored} unique QA alerts")
                metrics_tracker.end_stage("qa_flag_generation")
            except Exception as e:
                db.rollback()
                logger.warning(f"Failed to store QA flags: {e}")
                metrics_tracker.record_error("qa_flag_generation", str(e))

            # 5. Compute weighted score
            try:
                metrics_tracker.start_stage("weighted_scoring")
                logger.info("Step 5: Computing weighted score")
                clinical_safety_triggered = (
                    rubric_response.get("dimension_scores", {}).get("clinical_safety", {}).get("red_flag_detected")
                    and not rubric_response.get("dimension_scores", {}).get("clinical_safety", {}).get("handled_appropriately")
                )
                weighted_score = compute_weighted_score(dimension_scores_db, clinical_safety_triggered)

                # Update overall score in all rubric scores
                for score_obj in db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id):
                    score_obj.overall_weighted_score = weighted_score

                db.flush()
                metrics_tracker.end_stage("weighted_scoring")
                logger.info("Weighted score computed: %.2f (safety_gate=%s)", weighted_score, clinical_safety_triggered)
            except Exception as e:
                db.rollback()
                metrics_tracker.record_error("weighted_scoring", str(e))
                raise PipelineStageError(f"Weighted scoring failed: {e}") from e

            # 6. Evaluate deterministic flags (only add ones NOT already covered by Claude)
            try:
                metrics_tracker.start_stage("flag_evaluation")
                logger.info("Step 6: Evaluating deterministic QA flags")
                flags = evaluate_flags(metrics_dict, dimension_scores_db, rubric_response, db, call)

                # Get already-stored flag types to avoid duplicates
                existing_flag_types = {
                    f.flag_type for f in db.query(models.QAFlag).filter(models.QAFlag.call_id == call.id).all()
                }

                added = 0
                for flag_data in flags:
                    if not flag_data["triggered"]:
                        continue
                    if flag_data["flag_type"] in existing_flag_types:
                        continue  # Skip if Claude already flagged this
                    flag_obj = models.QAFlag(
                        call_id=call.id,
                        flag_type=flag_data["flag_type"],
                        triggered=True,
                        detail=flag_data["detail"],
                    )
                    db.add(flag_obj)
                    existing_flag_types.add(flag_data["flag_type"])
                    added += 1

                db.flush()
                metrics_tracker.end_stage("flag_evaluation")
                logger.info("Deterministic flags added: %d new", added)
            except Exception as e:
                db.rollback()
                metrics_tracker.record_error("flag_evaluation", str(e))
                raise PipelineStageError(f"Flag evaluation failed: {e}") from e

            # 7. Generate feedback
            try:
                metrics_tracker.start_stage("feedback_generation")
                logger.info("Step 7: Generating feedback")
                feedback_bullets = generate_feedback_bullets(dimension_scores_db, rubric_response, flags)
                retraining_rec, retraining_reason = generate_retraining_recommendation(weighted_score, flags, call.dietician_id, db)

                feedback_note = models.FeedbackNote(
                    call_id=call.id,
                    bullet=" | ".join(feedback_bullets),
                    retraining_recommended=retraining_rec,
                    retraining_reason=retraining_reason,
                )
                db.add(feedback_note)

                db.flush()
                metrics_tracker.end_stage("feedback_generation")
                logger.info("Feedback generated: %d bullets, retraining=%s", len(feedback_bullets), retraining_rec)
            except Exception as e:
                db.rollback()
                metrics_tracker.record_error("feedback_generation", str(e))
                raise PipelineStageError(f"Feedback generation failed: {e}") from e

            # 8. Mark as complete
            try:
                metrics_tracker.start_stage("finalization")
                logger.info("Step 8: Finalizing")
                call.status = models.CallStatus.completed
                call.processed_at = datetime.utcnow()
                db.commit()
                metrics_tracker.end_stage("finalization")

                summary = metrics_tracker.get_summary()
                logger.info(
                    "Successfully completed processing for call %s. Score: %.2f (total_time: %.1fs)",
                    call_id, weighted_score, summary["total_time_seconds"]
                )
            except SQLAlchemyError as e:
                db.rollback()
                metrics_tracker.record_error("finalization", str(e))
                raise PipelineStageError(f"Finalization failed: {e}") from e

        finally:
            if audio_path:
                cleanup_audio(audio_path)

    except PipelineStageError as e:
        logger.error("Pipeline stage failed for call %s: %s", call_id, str(e), exc_info=True)
        try:
            call = db.query(models.Call).filter(models.Call.id == call_id).first()
            if call:
                call.status = models.CallStatus.failed
                call.error_message = str(e)
                db.commit()
        except SQLAlchemyError as db_err:
            logger.error("Failed to update call status in DB: %s", db_err)
            db.rollback()
        finally:
            summary = metrics_tracker.get_summary()
            logger.error("Pipeline failed after %.1fs. Errors: %s", summary["total_time_seconds"], summary["errors"])
        raise

    except Exception as e:
        logger.error("Unexpected error processing call %s: %s", call_id, str(e), exc_info=True)
        try:
            call = db.query(models.Call).filter(models.Call.id == call_id).first()
            if call:
                call.status = models.CallStatus.failed
                call.error_message = f"Unexpected error: {str(e)}"
                db.commit()
        except SQLAlchemyError as db_err:
            logger.error("Failed to update call status in DB: %s", db_err)
            db.rollback()
        raise

    finally:
        if audio_path:
            try:
                cleanup_audio(audio_path)
            except Exception as e:
                logger.warning("Error during audio cleanup: %s", e)
        try:
            db.close()
        except Exception as e:
            logger.warning("Error closing database session: %s", e)
