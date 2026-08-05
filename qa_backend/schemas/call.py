from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional
from uuid import UUID


class CallCreate(BaseModel):
    dietician_id: Optional[UUID] = None
    dietician_name: Optional[str] = None
    patient_id: str
    patient_name: Optional[str] = None
    appointment_id: str
    call_datetime: datetime
    recording_url: str
    call_duration_seconds: Optional[int] = None


class CallResponse(BaseModel):
    id: UUID
    dietician_id: UUID
    patient_id: str
    patient_name: Optional[str]
    appointment_id: str
    call_datetime: datetime
    recording_url: str
    call_duration_seconds: Optional[int]
    status: str
    created_at: datetime
    processed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class CallDetailResponse(CallResponse):
    transcript: Optional[dict] = None
    metrics: Optional[dict] = None
    rubric_scores: Optional[list] = None
    qa_flags: Optional[list] = None
    qaAlerts: Optional[list] = None
    feedback_notes: Optional[dict] = None
    overall_weighted_score: Optional[float] = None
    scores: Optional[dict] = None
    insights: Optional[dict] = None
    entities: Optional[dict] = None
    dietician_name: Optional[str] = None
    raw_transcript: Optional[str] = None
    reconstructed_transcript: Optional[str] = None


class ValidationReportRow(BaseModel):
    row_num: int
    status: str  # valid, invalid
    reason: Optional[str] = None


class ValidationReport(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows: list[ValidationReportRow]
    batch_id: Optional[UUID] = None
