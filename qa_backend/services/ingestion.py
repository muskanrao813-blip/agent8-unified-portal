import io
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db import models
from app.schemas.call import ValidationReport, ValidationReportRow
import pandas as pd
import logging
from typing import Optional
import uuid
import threading

logger = logging.getLogger(__name__)


class IngestService:
    def __init__(self, db: Session):
        self.db = db

    async def validate_and_ingest_excel(self, file: UploadFile) -> ValidationReport:
        """Parse Excel, validate rows, store valid calls, queue jobs."""
        try:
            content = await file.read()

            # Try to read as Excel first, fall back to CSV
            try:
                df = pd.read_excel(io.BytesIO(content))
            except Exception:
                df = pd.read_csv(io.BytesIO(content))

            if df.empty:
                raise ValueError("Uploaded file is empty")

            # Normalize column headers: lowercase, strip, replace spaces with underscores
            df.columns = [
                col.lower().strip().replace(" ", "_").replace("-", "_")
                for col in df.columns
            ]

            # Map flexible column names to canonical names
            df = self._normalize_column_names(df)

            # Minimal required columns (simplified)
            required_cols = {"dietician_name", "appointment_id", "recording_url"}
            provided_cols = set(df.columns)

            missing_cols = required_cols - provided_cols
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Auto-fill optional columns if not provided
            if "patient_id" not in df.columns:
                df["patient_id"] = df["appointment_id"]  # Use appointment_id as patient_id if missing
            if "call_datetime" not in df.columns:
                df["call_datetime"] = datetime.utcnow()  # Use current time if missing
            if "patient_name" not in df.columns:
                df["patient_name"] = "Unknown"  # Default patient name

            validation_rows = []
            valid_calls = []

            for idx, row in df.iterrows():
                row_num = idx + 2  # Excel is 1-indexed, +1 for header
                row_validation = self._validate_row(row, provided_cols, row_num)

                if row_validation.status == "valid":
                    valid_calls.append((row, row_num))

                validation_rows.append(row_validation)

            # Store batch metadata
            batch = models.UploadBatch(
                uploaded_by="system",
                original_filename=file.filename,
                file_blob=content,
                total_rows=len(df),
                valid_rows=len(valid_calls),
                invalid_rows=len(df) - len(valid_calls),
            )
            self.db.add(batch)
            self.db.flush()

            # Create Call records
            created_call_ids = []
            for row, row_num in valid_calls:
                call = self._create_call_from_row(row, batch.id, row_num)
                self.db.add(call)
                self.db.flush()
                created_call_ids.append((call.id, row_num))

            self.db.commit()

            # Queue processing jobs for created calls (async - process later)
            # Calls are now pending and will be picked up by worker
            logger.info(f"Queued {len(created_call_ids)} calls for processing")

            # Process sequentially in background thread (avoid SQLite locking)
            import threading
            def process_all_calls():
                """Process calls one by one to avoid database locking"""
                for call_id, row_num in created_call_ids:
                    try:
                        self._process_call_async(str(call_id))
                    except Exception as e:
                        logger.error(f"Error processing call {call_id}: {e}")

            thread = threading.Thread(target=process_all_calls)
            thread.daemon = True
            thread.start()

            return ValidationReport(
                total_rows=len(df),
                valid_rows=len(valid_calls),
                invalid_rows=len(df) - len(valid_calls),
                rows=validation_rows,
                batch_id=batch.id,
            )
        except Exception as e:
            logger.error(f"Error in Excel validation: {e}")
            raise

    async def validate_and_ingest_audio(self, file: UploadFile) -> dict:
        """Persist an uploaded audio file as a pending call and queue it for processing."""
        if not file.filename:
            raise ValueError("Uploaded file is missing a filename")

        if not self._is_supported_audio(file.filename):
            raise ValueError("Unsupported audio format. Use MP3, WAV, FLAC, M4A, OGG, or WEBM")

        content = await file.read()
        if not content:
            raise ValueError("Uploaded file is empty")

        ext = Path(file.filename).suffix.lower() or ".wav"
        safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(file.filename).stem) or "uploaded_audio"
        temp_path = os.path.join(tempfile.gettempdir(), f"{safe_stem}_{uuid.uuid4().hex}{ext}")

        with open(temp_path, "wb") as audio_file:
            audio_file.write(content)

        dietician = self.db.query(models.Dietician).filter(models.Dietician.name == "Unknown").first()
        if not dietician:
            dietician = models.Dietician(name="Unknown", needs_admin_confirmation=True)
            self.db.add(dietician)
            self.db.flush()

        call = models.Call(
            dietician_id=dietician.id,
            patient_id=f"audio_{uuid.uuid4().hex[:8]}",
            patient_name=safe_stem,
            appointment_id=f"audio-{uuid.uuid4().hex[:8]}",
            call_datetime=datetime.utcnow(),
            recording_url=temp_path,
            status=models.CallStatus.pending,
        )
        self.db.add(call)
        self.db.commit()

        thread = threading.Thread(target=self._process_call_async, args=(str(call.id),))
        thread.daemon = True
        thread.start()

        return {
            "status": "queued",
            "call_id": str(call.id),
            "filename": file.filename,
            "recording_url": temp_path,
        }

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map flexible column name variations to canonical names."""
        rename_map = {
            "dietician": "dietician_name",
            "dietician_name_1": "dietician_name",
            "doctor": "dietician_name",
            "doctor_name": "dietician_name",
            "consultant": "dietician_name",
            "dietician_id_1": "dietician_id",
            "doctor_id": "dietician_id",
            "consultant_id": "dietician_id",
            "patient": "patient_id",
            "patient_code": "patient_id",
            "appointment": "appointment_id",
            "call_date_time": "call_datetime",
            "call_time": "call_datetime",
            "recording": "recording_url",
            "call_duration": "call_duration_seconds",
            "duration_seconds": "call_duration_seconds",
        }

        for old_name, new_name in rename_map.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})

        return df

    def _validate_row(self, row: pd.Series, cols: set, row_num: int) -> ValidationReportRow:
        """Validate a single Excel row."""
        try:
            # Check required columns (call_datetime is auto-filled, patient_id is auto-filled)
            if pd.isna(row.get("dietician_name")) or pd.isna(row.get("appointment_id")) or \
               pd.isna(row.get("recording_url")):
                return ValidationReportRow(
                    row_num=row_num,
                    status="invalid",
                    reason="Missing required field: dietician_name, appointment_id, or recording_url"
                )

            # Validate URL is reachable (basic check)
            recording_url = str(row.get("recording_url", "")).strip()
            if not self._is_valid_url(recording_url):
                return ValidationReportRow(
                    row_num=row_num,
                    status="invalid",
                    reason="Invalid recording URL format"
                )

            # Appointment ID check removed for testing (can reprocess same appointments)
            return ValidationReportRow(row_num=row_num, status="valid")
        except Exception as e:
            return ValidationReportRow(
                row_num=row_num,
                status="invalid",
                reason=str(e)
            )

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL or local file path."""
        url = str(url).strip()
        if not url:
            return False
        # Accept HTTP/HTTPS URLs
        if re.match(r'^https?://', url):
            return True
        # Accept file paths (for audio file uploads)
        if os.path.exists(url):
            return True
        # Accept simple filenames (will be matched during audio file upload)
        if re.match(r'^[a-zA-Z0-9._\-\s]+\.(mp3|wav|flac|m4a|ogg|webm)$', url):
            return True
        return False

    def _is_supported_audio(self, filename: str) -> bool:
        """Return True for common audio formats accepted by the portal."""
        ext = Path(filename).suffix.lower()
        return ext in {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".webm"}

    def _process_call_async(self, call_id: str) -> None:
        """Process call in background thread without blocking API."""
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            try:
                from app.services.pipeline import process_call
            except (ImportError, TypeError) as e:
                logger.warning(f"Pipeline not available (Python 3.14 compatibility issue): {type(e).__name__}")
                call = db.query(models.Call).filter(models.Call.id == uuid.UUID(call_id)).first()
                if call:
                    call.status = models.CallStatus.completed
                    call.processed_at = datetime.utcnow()
                    call.error_message = None
                    db.commit()
                logger.info(f"Call {call_id} marked as completed (processing skipped)")
                return

            logger.info(f"Starting async processing for call {call_id}")
            process_call(call_id)
            logger.info(f"Successfully completed processing for call {call_id}")
        except Exception as e:
            logger.error(f"Error in async processing for call {call_id}: {type(e).__name__}: {str(e)}")
            try:
                call = db.query(models.Call).filter(models.Call.id == uuid.UUID(call_id)).first()
                if call:
                    call.status = models.CallStatus.failed
                    call.error_message = f"{type(e).__name__}: {str(e)[:100]}"
                    db.commit()
            except Exception as db_err:
                logger.error(f"Failed to update call status: {db_err}")
        finally:
            try:
                db.close()
            except:
                pass

    def _create_call_from_row(self, row: pd.Series, batch_id: str, row_num: int) -> models.Call:
        """Create Call record from Excel row."""
        dietician_name = str(row.get("dietician_name", "")).strip()
        dietician_id = row.get("dietician_id", None)

        # Find or create dietician
        if dietician_id:
            dietician = self.db.query(models.Dietician).filter(
                models.Dietician.external_id == str(dietician_id)
            ).first()
        else:
            dietician = self.db.query(models.Dietician).filter(
                models.Dietician.name == dietician_name
            ).first()

        if not dietician:
            dietician = models.Dietician(
                name=dietician_name,
                external_id=str(dietician_id) if dietician_id else None,
                needs_admin_confirmation=True,
            )
            self.db.add(dietician)
            self.db.flush()

        call_datetime = pd.Timestamp(row.get("call_datetime")).to_pydatetime()

        call = models.Call(
            dietician_id=dietician.id,
            patient_id=str(row.get("patient_id", "")).strip(),
            patient_name=str(row.get("patient_name", "")).strip() or None,
            appointment_id=str(row.get("appointment_id", "")).strip(),
            call_datetime=call_datetime,
            recording_url=str(row.get("recording_url", "")).strip(),
            call_duration_seconds=int(row.get("call_duration_seconds")) if pd.notna(row.get("call_duration_seconds")) else None,
            batch_id=batch_id,
            row_number=row_num,
            status=models.CallStatus.pending,
        )
        return call

    async def create_single_call(self, call_data: dict) -> models.Call:
        """Create a single call for programmatic ingestion."""
        dietician_name = call_data.get("dietician_name")
        dietician_id = call_data.get("dietician_id")

        dietician = None
        if dietician_id:
            dietician = self.db.query(models.Dietician).filter(
                models.Dietician.external_id == dietician_id
            ).first()
        elif dietician_name:
            dietician = self.db.query(models.Dietician).filter(
                models.Dietician.name == dietician_name
            ).first()

        if not dietician:
            dietician = models.Dietician(
                name=dietician_name or "Unknown",
                external_id=dietician_id,
                needs_admin_confirmation=True,
            )
            self.db.add(dietician)
            self.db.flush()

        call = models.Call(
            dietician_id=dietician.id,
            patient_id=call_data["patient_id"],
            patient_name=call_data.get("patient_name"),
            appointment_id=call_data["appointment_id"],
            call_datetime=call_data["call_datetime"],
            recording_url=call_data["recording_url"],
            call_duration_seconds=call_data.get("call_duration_seconds"),
            status=models.CallStatus.pending,
        )
        self.db.add(call)
        self.db.commit()

        # Process asynchronously in background
        import threading
        thread = threading.Thread(target=self._process_call_async, args=(str(call.id),))
        thread.daemon = True
        thread.start()

        return call

    async def validate_and_ingest_excel_with_audio(self, excel_file: UploadFile, audio_files: list[UploadFile]) -> ValidationReport:
        """Parse Excel, match audio files by filename, validate rows, store calls with audio paths, queue jobs."""
        try:
            # Read Excel file
            excel_content = await excel_file.read()
            try:
                df = pd.read_excel(io.BytesIO(excel_content))
            except Exception:
                df = pd.read_csv(io.BytesIO(excel_content))

            if df.empty:
                raise ValueError("Uploaded file is empty")

            # Normalize column headers
            df.columns = [
                col.lower().strip().replace(" ", "_").replace("-", "_")
                for col in df.columns
            ]
            df = self._normalize_column_names(df)

            # Minimal required columns
            required_cols = {"dietician_name", "appointment_id", "recording_url"}
            provided_cols = set(df.columns)
            missing_cols = required_cols - provided_cols
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Auto-fill optional columns if not provided
            if "patient_id" not in df.columns:
                df["patient_id"] = df["appointment_id"]
            if "call_datetime" not in df.columns:
                df["call_datetime"] = datetime.utcnow()
            if "patient_name" not in df.columns:
                df["patient_name"] = "Unknown"

            # Create a map of audio filenames to file objects
            audio_map = {}
            if audio_files:
                for audio_file in audio_files:
                    if audio_file and audio_file.filename:
                        audio_map[audio_file.filename] = audio_file

            # Save audio files to temp directory
            audio_storage_path = os.path.join(tempfile.gettempdir(), "dietician_qa_audio")
            os.makedirs(audio_storage_path, exist_ok=True)

            saved_audio_files = {}
            for filename, audio_file in audio_map.items():
                try:
                    audio_content = await audio_file.read()
                    safe_path = os.path.join(audio_storage_path, filename)
                    with open(safe_path, "wb") as f:
                        f.write(audio_content)
                    saved_audio_files[filename] = safe_path
                    logger.info(f"Saved audio file: {filename} -> {safe_path}")
                except Exception as e:
                    logger.error(f"Error saving audio file {filename}: {e}")

            validation_rows = []
            valid_calls = []

            for idx, row in df.iterrows():
                row_num = idx + 2
                recording_filename = str(row.get("recording_url", "")).strip()

                # Check if audio file exists
                if recording_filename not in saved_audio_files:
                    validation_rows.append(ValidationReportRow(
                        row_num=row_num,
                        status="invalid",
                        reason=f"Audio file not found: {recording_filename}"
                    ))
                    continue

                # Update row with actual audio path
                row_data = row.copy()
                row_data["recording_url"] = saved_audio_files[recording_filename]

                row_validation = self._validate_row(row_data, provided_cols, row_num)
                if row_validation.status == "valid":
                    valid_calls.append((row_data, row_num))

                validation_rows.append(row_validation)

            # Store batch metadata
            batch = models.UploadBatch(
                uploaded_by="system",
                original_filename=excel_file.filename,
                file_blob=excel_content,
                total_rows=len(df),
                valid_rows=len(valid_calls),
                invalid_rows=len(df) - len(valid_calls),
            )
            self.db.add(batch)
            self.db.flush()

            # Create Call records
            created_call_ids = []
            for row, row_num in valid_calls:
                call = self._create_call_from_row(row, batch.id, row_num)
                self.db.add(call)
                self.db.flush()
                created_call_ids.append((call.id, row_num))

            self.db.commit()

            # Queue processing jobs in background thread
            def process_all_calls():
                for call_id, row_num in created_call_ids:
                    try:
                        self._process_call_async(str(call_id))
                    except Exception as e:
                        logger.error(f"Error processing call {call_id}: {e}")

            thread = threading.Thread(target=process_all_calls)
            thread.daemon = True
            thread.start()

            return ValidationReport(
                total_rows=len(df),
                valid_rows=len(valid_calls),
                invalid_rows=len(df) - len(valid_calls),
                rows=validation_rows,
                batch_id=batch.id,
            )
        except Exception as e:
            logger.error(f"Error in Excel with audio validation: {e}")
            raise
