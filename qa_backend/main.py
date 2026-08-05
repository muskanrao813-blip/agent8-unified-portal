from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from app.db.session import get_db, engine
from app.db.models import Base
from app.api import calls, dieticians, clinical_calls

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dietician Call QA & Analysis Agent", version="0.1.0")

@app.on_event("startup")
def startup_event():
    """Create all database tables on startup"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")

# Add CORS middleware - allow development & production origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Development (localhost)
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        # Production (Netlify)
        "https://consultation-call-quality-analysis.netlify.app",
        "https://rainbow-biscotti-eb81b0.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calls.router, prefix="/api", tags=["calls"])
app.include_router(dieticians.router, prefix="/api", tags=["dieticians"])
app.include_router(clinical_calls.router, prefix="/api", tags=["clinical"])


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/debug/logs")
def get_logs():
    """Get the last 100 lines of server logs for debugging"""
    import subprocess
    try:
        # Read the last 100 lines of the server log
        result = subprocess.run(
            ["powershell", "-Command", "Get-Content $env:TEMP\\server.log -Tail 100"],
            capture_output=True,
            text=True,
            timeout=5
        )
        logs = result.stdout if result.stdout else "No logs yet"
        return {"logs": logs}
    except Exception as e:
        return {"logs": f"Error reading logs: {str(e)}", "status": "error"}


@app.get("/api/debug/calls")
def get_processing_status():
    """Get status of all calls for debugging"""
    try:
        from app.db.session import SessionLocal
        from app.db import models

        db = SessionLocal()
        try:
            calls = db.query(models.Call).order_by(models.Call.created_at.desc()).limit(10).all()

            result = []
            for call in calls:
                try:
                    trans = db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first()
                    metrics = db.query(models.CallMetrics).filter(models.CallMetrics.call_id == call.id).first()
                    scores = db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).first()

                    # Get transcript text from either raw_transcript_json or raw_transcript
                    transcript_text = ""
                    if trans:
                        if hasattr(trans, 'raw_transcript_json') and trans.raw_transcript_json:
                            if isinstance(trans.raw_transcript_json, dict):
                                transcript_text = trans.raw_transcript_json.get("text", "")
                            else:
                                transcript_text = str(trans.raw_transcript_json)
                        elif hasattr(trans, 'raw_transcript') and trans.raw_transcript:
                            transcript_text = trans.raw_transcript

                    result.append({
                        "id": str(call.id),
                        "status": str(call.status),
                        "created": str(call.created_at),
                        "patient_name": call.patient_name,
                        "appointment_id": call.appointment_id,
                        "recording_url": call.recording_url[:50] + "..." if call.recording_url and len(call.recording_url) > 50 else call.recording_url,
                        "transcript_exists": trans is not None,
                        "transcript_provider": trans.provider if trans else None,
                        "transcript_text_length": len(transcript_text) if transcript_text else 0,
                        "metrics_exists": metrics is not None,
                        "scores_exists": scores is not None,
                        "overall_score": scores.overall_weighted_score if scores else None,
                        "error": call.error_message
                    })
                except Exception as e:
                    result.append({
                        "error": f"Error processing call: {str(e)}"
                    })

            return {"calls": result, "total_calls": len(calls)}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}")
        return {
            "status": "error",
            "message": f"Database error: {str(e)}",
            "hint": "Database may not be initialized yet"
        }


@app.get("/api/debug/process-call/{call_id}")
def debug_process_call(call_id: str):
    """Manually trigger processing for a specific call (for debugging)"""
    try:
        from app.services.pipeline import process_call
        import uuid

        # Verify call exists
        from app.db.session import SessionLocal
        from app.db import models
        db = SessionLocal()

        try:
            call_uuid = uuid.UUID(call_id)
            call = db.query(models.Call).filter(models.Call.id == call_uuid).first()
            if not call:
                return {"status": "error", "message": f"Call {call_id} not found"}

            # Try to process it
            logger.info(f"Manual processing triggered for call {call_id}")
            process_call(call_id)

            # Check result
            call = db.query(models.Call).filter(models.Call.id == call_uuid).first()
            return {
                "status": "completed",
                "call_id": call_id,
                "call_status": str(call.status),
                "error_message": call.error_message
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"{type(e).__name__}: {str(e)}",
                "call_id": call_id
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in manual processing: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/debug/dietician/{dietician_name}")
def check_dietician_calls(dietician_name: str):
    """Check all calls for a specific dietician"""
    try:
        from app.db.session import SessionLocal
        from app.db import models

        db = SessionLocal()
        try:
            # Find dietician
            dietician = db.query(models.Dietician).filter(
                models.Dietician.name.ilike(f"%{dietician_name}%")
            ).first()

            if not dietician:
                return {"status": "error", "message": f"Dietician '{dietician_name}' not found"}

            # Get all calls for this dietician
            calls = db.query(models.Call).filter(
                models.Call.dietician_id == dietician.id
            ).order_by(models.Call.created_at.desc()).all()

            call_summaries = []
            for call in calls:
                metrics = db.query(models.CallMetrics).filter(models.CallMetrics.call_id == call.id).first()
                scores = db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).all()
                qa_flags = db.query(models.QAFlag).filter(models.QAFlag.call_id == call.id).all()

                dimension_scores = {s.dimension: s.score for s in scores}
                overall = scores[0].overall_weighted_score if scores else 0

                call_summaries.append({
                    "call_id": str(call.id),
                    "appointment_id": call.appointment_id,
                    "patient_name": call.patient_name,
                    "status": str(call.status),
                    "duration_seconds": metrics.duration_seconds if metrics else 0,
                    "patient_talk_pct": metrics.patient_talk_ratio_pct if metrics else 0,
                    "time_to_plan_sec": metrics.time_to_first_plan_mention_seconds if metrics else 0,
                    "scores": {
                        "greeting": dimension_scores.get("greeting", 0),
                        "empathy": dimension_scores.get("empathy", 0),
                        "compliance": dimension_scores.get("compliance", 0),
                        "technical": dimension_scores.get("technical", 0),
                        "overall_weighted": overall
                    },
                    "critical_flags": [f.flag_type for f in qa_flags if f.triggered]
                })

            # Calculate averages
            if call_summaries:
                avg_score = sum(c["scores"]["overall_weighted"] for c in call_summaries) / len(call_summaries)
                avg_compliance = sum(c["scores"]["compliance"] for c in call_summaries) / len(call_summaries)
            else:
                avg_score = 0
                avg_compliance = 0

            return {
                "dietician": dietician.name,
                "total_calls": len(call_summaries),
                "average_overall_score": round(avg_score, 1),
                "average_compliance_score": round(avg_compliance, 1),
                "calls": call_summaries
            }
        finally:
            db.close()
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()[:300]
        }


@app.get("/api/debug/call/{call_id}")
def check_specific_call(call_id: str):
    """Check a specific call by ID"""
    try:
        from app.db.session import SessionLocal
        from app.db import models
        import uuid

        db = SessionLocal()
        try:
            call_uuid = uuid.UUID(call_id)
            call = db.query(models.Call).filter(models.Call.id == call_uuid).first()

            if not call:
                return {"status": "error", "message": f"Call {call_id} not found"}

            # Get all related data
            transcript = db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first()
            metrics = db.query(models.CallMetrics).filter(models.CallMetrics.call_id == call.id).first()
            scores = db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).all()
            qa_flags = db.query(models.QAFlag).filter(models.QAFlag.call_id == call.id).all()

            transcript_text = ""
            if transcript and transcript.raw_transcript_json:
                raw_json = transcript.raw_transcript_json
                transcript_text = raw_json.get("text", "")[:2000]  # First 2000 chars

            return {
                "call_id": str(call.id),
                "status": str(call.status),
                "appointment_id": call.appointment_id,
                "error_message": call.error_message,
                "transcript_preview": transcript_text,
                "metrics": {
                    "duration_seconds": metrics.duration_seconds if metrics else None,
                    "dietician_talk_ratio": metrics.dietician_talk_ratio_pct if metrics else None,
                    "patient_talk_ratio": metrics.patient_talk_ratio_pct if metrics else None,
                    "interruption_count": metrics.interruption_count if metrics else None,
                    "avg_response_latency": metrics.avg_response_latency_seconds if metrics else None,
                    "time_to_first_plan": metrics.time_to_first_plan_mention_seconds if metrics else None,
                },
                "scores": {
                    "dimensions": [{"name": s.dimension, "score": s.score, "overall_weighted": s.overall_weighted_score} for s in scores],
                    "qa_flags": [{"type": f.flag_type, "triggered": f.triggered, "detail": f.detail} for f in qa_flags]
                }
            }
        finally:
            db.close()
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()[:300]
        }


@app.get("/api/debug/check-recent-call")
def check_recent_call():
    """Check the most recent call and show what happened"""
    try:
        from app.db.session import SessionLocal
        from app.db import models

        db = SessionLocal()
        try:
            # Get most recent call
            call = db.query(models.Call).order_by(models.Call.created_at.desc()).first()

            if not call:
                return {"status": "error", "message": "No calls found"}

            # Get all related data
            transcript = db.query(models.Transcript).filter(models.Transcript.call_id == call.id).first()
            metrics = db.query(models.CallMetrics).filter(models.CallMetrics.call_id == call.id).first()
            scores = db.query(models.RubricScore).filter(models.RubricScore.call_id == call.id).all()
            qa_flags = db.query(models.QAFlag).filter(models.QAFlag.call_id == call.id).all()

            return {
                "call_id": str(call.id),
                "status": str(call.status),
                "error_message": call.error_message,
                "transcript": {
                    "exists": transcript is not None,
                    "provider": transcript.provider if transcript else None,
                    "text_length": len(str(transcript.raw_transcript_json)) if transcript and transcript.raw_transcript_json else 0,
                    "diarized_segments": len(transcript.diarized_segments) if transcript and transcript.diarized_segments else 0
                },
                "metrics": {
                    "exists": metrics is not None,
                    "duration": metrics.duration_seconds if metrics else None,
                    "dietician_talk": metrics.dietician_talk_ratio_pct if metrics else None,
                    "patient_talk": metrics.patient_talk_ratio_pct if metrics else None
                },
                "scores": {
                    "count": len(scores),
                    "dimensions": [s.dimension for s in scores],
                    "values": {s.dimension: s.score for s in scores},
                    "overall": scores[0].overall_weighted_score if scores else None,
                    "raw_response_sample": str(scores[0].raw_llm_response)[:200] if scores and scores[0].raw_llm_response else None
                },
                "qa_flags": {
                    "count": len(qa_flags),
                    "flags": [{"type": f.flag_type, "triggered": f.triggered, "detail": f.detail} for f in qa_flags]
                }
            }
        finally:
            db.close()
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()[:300]
        }


@app.get("/api/debug/test-gemini-raw")
def test_gemini_raw():
    """Test raw Gemini response to see exact output"""
    try:
        import os
        from google import genai
        from google.genai import types
        import httpx

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {"status": "error", "message": "GEMINI_API_KEY not set"}

        http_client = httpx.Client(verify=False)
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(httpx_client=http_client),
        )

        # Simple test prompt
        test_prompt = """You are a QA expert. Return ONLY valid JSON (no markdown):
{
  "test": "hello",
  "status": "working"
}"""

        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=test_prompt,
        )

        response_text = response.text.strip()

        return {
            "status": "success",
            "raw_response": response_text[:1000],
            "response_length": len(response_text),
            "is_json": response_text.startswith("{"),
            "first_100_chars": response_text[:100],
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"{type(e).__name__}: {str(e)}",
            "traceback": traceback.format_exc()[:300]
        }


@app.get("/api/debug/test-gemini-analyzer")
def test_gemini_analyzer():
    """Test Gemini analyzer with sample data"""
    try:
        from app.services.llm.gemini_analyzer import GeminiAnalyzer

        analyzer = GeminiAnalyzer()

        # Sample transcript segments
        test_segments = [
            {"speaker": "dietician", "text": "Hello, how are you feeling today?", "start_s": 0, "end_s": 3},
            {"speaker": "patient", "text": "I'm doing well, thank you for asking", "start_s": 3, "end_s": 8},
            {"speaker": "dietician", "text": "Do you have any medical conditions I should know about?", "start_s": 8, "end_s": 15},
            {"speaker": "patient", "text": "I have diabetes and hypertension", "start_s": 15, "end_s": 20},
            {"speaker": "dietician", "text": "I see. Let me create a personalized diet plan for you", "start_s": 20, "end_s": 28},
        ]

        # Sample metrics
        test_metrics = {
            "duration_seconds": 300,
            "dietician_talk_ratio_pct": 45,
            "patient_talk_ratio_pct": 35,
            "interruption_count": 2,
            "avg_response_latency_seconds": 2.5,
            "time_to_first_plan_mention_seconds": 180,
            "silence_pct": 10,
        }

        result = analyzer.analyze_all_dimensions(
            test_segments,
            test_metrics,
            "test-call-id",
            "Dr. Test",
            "patient-001",
            "Diabetes"
        )

        return {
            "status": "success",
            "message": "Gemini analyzer test completed",
            "result_keys": list(result.keys()),
            "has_scores": "scores" in result,
            "has_sop_compliance": "sop_compliance" in result,
            "has_insights": "insights" in result,
            "has_qa_alerts": "qa_alerts" in result,
            "result_summary": {
                "scores": result.get("scores"),
                "sop_compliance_score": result.get("sop_compliance", {}).get("compliance_score"),
                "insights_summary": result.get("insights", {}).get("summary"),
            }
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"{type(e).__name__}: {str(e)}",
            "traceback": traceback.format_exc()[:500]
        }


@app.get("/api/debug/test-gemini")
def test_gemini():
    """Test if Gemini API is working"""
    import os
    api_key = os.getenv("GEMINI_API_KEY", "NOT_SET")

    if api_key == "NOT_SET":
        return {"status": "error", "message": "GEMINI_API_KEY environment variable not set"}

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        # Simple test
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents="Say 'Gemini is working' in one sentence"
        )
        return {
            "status": "success",
            "message": response.text[:100],
            "api_key_set": True
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"{type(e).__name__}: {str(e)}",
            "api_key_set": api_key != "NOT_SET"
        }


@app.get("/api/debug/test-claude")
def test_claude():
    """Test if Claude CLI is available and working"""
    import subprocess
    import shutil
    import os
    import pathlib

    results = {
        "status": "checking",
        "claude_available": False,
        "search_results": {},
        "diagnostics": {}
    }

    # 1. Check PATH environment variable
    current_path = os.environ.get("PATH", "NOT SET")
    results["diagnostics"]["current_path"] = current_path[:300] if current_path != "NOT SET" else current_path

    # 2. Try which command
    try:
        which_result = subprocess.run(["which", "claude"], capture_output=True, text=True, timeout=5)
        results["diagnostics"]["which_claude"] = which_result.stdout.strip() or "not found"
    except Exception as e:
        results["diagnostics"]["which_claude"] = f"error: {str(e)}"

    # 3. Search in many possible locations
    search_locations = [
        shutil.which("claude"),
        "/usr/local/bin/claude",
        "/usr/bin/claude",
        "/opt/render/.npm-global/bin/claude",
        "/root/.npm-global/bin/claude",
        "/home/render/.npm-global/bin/claude",
        "/usr/local/lib/node_modules/.bin/claude",
    ]

    claude_path = None
    for loc in search_locations:
        if loc:
            exists = pathlib.Path(loc).exists()
            results["search_results"][loc] = "exists" if exists else "not found"
            if exists and not claude_path:
                claude_path = loc

    # 4. Try npm to find global bin path
    try:
        npm_result = subprocess.run(["npm", "config", "get", "prefix"], capture_output=True, text=True, timeout=5)
        npm_prefix = npm_result.stdout.strip()
        npm_claude = os.path.join(npm_prefix, "bin", "claude")
        results["diagnostics"]["npm_prefix"] = npm_prefix
        results["search_results"][npm_claude] = "exists" if pathlib.Path(npm_claude).exists() else "not found"
        if pathlib.Path(npm_claude).exists() and not claude_path:
            claude_path = npm_claude
    except Exception as e:
        results["diagnostics"]["npm_prefix_error"] = str(e)

    # 5. If found, test it
    if claude_path:
        results["claude_path"] = claude_path
        try:
            version_result = subprocess.run([claude_path, "--version"], capture_output=True, text=True, timeout=5)
            if version_result.returncode == 0:
                results["status"] = "success"
                results["claude_available"] = True
                results["message"] = version_result.stdout.strip()
                return results
            else:
                results["status"] = "error"
                results["message"] = f"Exit code {version_result.returncode}: {version_result.stderr}"
                results["diagnostics"]["version_command_error"] = version_result.stderr
        except Exception as e:
            results["status"] = "error"
            results["message"] = f"{type(e).__name__}: {str(e)}"
            results["diagnostics"]["version_command_exception"] = str(e)
    else:
        results["status"] = "not_found"
        results["message"] = "Claude CLI not found in any location"
        results["fallback_analyzer"] = "Using Gemini API for QA analysis"

    return results


@app.get("/")
def root():
    return {
        "name": "Dietician Call QA & Analysis Agent",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "note": "Frontend available at http://localhost:3001"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
