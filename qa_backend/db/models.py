from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, LargeBinary,
    ForeignKey, Enum as SQLEnum, TIMESTAMP, JSON, UniqueConstraint, TypeDecorator
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid
import enum


class GUID(TypeDecorator):
    """Platform-independent GUID type for SQLite/PostgreSQL."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, str):
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value) if isinstance(value, str) else value

Base = declarative_base()


class CallStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Dietician(Base):
    __tablename__ = "dieticians"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    external_id = Column(String(255), nullable=True, unique=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    needs_admin_confirmation = Column(Boolean, default=False)

    calls = relationship("Call", back_populates="dietician")


class UploadBatch(Base):
    __tablename__ = "upload_batches"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    uploaded_by = Column(String(255), nullable=True)
    uploaded_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    original_filename = Column(String(255), nullable=False)
    file_blob = Column(LargeBinary, nullable=False)
    total_rows = Column(Integer, nullable=False)
    valid_rows = Column(Integer, nullable=False)
    invalid_rows = Column(Integer, nullable=False)

    calls = relationship("Call", back_populates="batch")


class Call(Base):
    __tablename__ = "calls"
    # Unique constraint removed temporarily for testing (can reprocess same appointments)

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    dietician_id = Column(GUID(), ForeignKey("dieticians.id"), nullable=False)
    patient_id = Column(String(255), nullable=False)
    patient_name = Column(String(255), nullable=True)
    appointment_id = Column(String(255), nullable=False)
    call_datetime = Column(TIMESTAMP, nullable=False)
    recording_url = Column(String(2048), nullable=False)
    call_duration_seconds = Column(Integer, nullable=True)
    status = Column(SQLEnum(CallStatus), nullable=False, default=CallStatus.pending)
    batch_id = Column(GUID(), ForeignKey("upload_batches.id"), nullable=True)
    row_number = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    processed_at = Column(TIMESTAMP, nullable=True)
    error_message = Column(Text, nullable=True)

    dietician = relationship("Dietician", back_populates="calls")
    batch = relationship("UploadBatch", back_populates="calls")
    transcript = relationship("Transcript", back_populates="call", uselist=False, cascade="all, delete-orphan")
    metrics = relationship("CallMetrics", back_populates="call", uselist=False, cascade="all, delete-orphan")
    rubric_scores = relationship("RubricScore", back_populates="call", cascade="all, delete-orphan")
    qa_flags = relationship("QAFlag", back_populates="call", cascade="all, delete-orphan")
    feedback_notes = relationship("FeedbackNote", back_populates="call", uselist=False, cascade="all, delete-orphan")


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    call_id = Column(GUID(), ForeignKey("calls.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    raw_transcript_json = Column(JSON, nullable=False)
    diarized_segments = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    call = relationship("Call", back_populates="transcript")


class CallMetrics(Base):
    __tablename__ = "call_metrics"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    call_id = Column(GUID(), ForeignKey("calls.id"), nullable=False)
    duration_seconds = Column(Float, nullable=False)
    dietician_talk_ratio_pct = Column(Float, nullable=False)
    patient_talk_ratio_pct = Column(Float, nullable=False)
    interruption_count = Column(Integer, nullable=False)
    avg_response_latency_seconds = Column(Float, nullable=True)
    time_to_first_plan_mention_seconds = Column(Float, nullable=True)
    silence_pct = Column(Float, nullable=False)
    off_topic_time_pct = Column(Float, default=0.0)

    call = relationship("Call", back_populates="metrics")


class RubricScore(Base):
    __tablename__ = "rubric_scores"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    call_id = Column(GUID(), ForeignKey("calls.id"), nullable=False)
    dimension = Column(String(50), nullable=False)
    score = Column(Float, nullable=False)
    evidence = Column(JSON, nullable=False)
    sub_criteria = Column(JSON, nullable=False)
    raw_llm_response = Column(JSON, nullable=False)
    overall_weighted_score = Column(Float, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    call = relationship("Call", back_populates="rubric_scores")


class QAFlag(Base):
    __tablename__ = "qa_flags"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    call_id = Column(GUID(), ForeignKey("calls.id"), nullable=False)
    flag_type = Column(String(100), nullable=False)
    triggered = Column(Boolean, nullable=False)
    detail = Column(Text, nullable=True)

    call = relationship("Call", back_populates="qa_flags")


class FeedbackNote(Base):
    __tablename__ = "feedback_notes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    call_id = Column(GUID(), ForeignKey("calls.id"), nullable=False)
    bullet = Column(Text, nullable=False)
    retraining_recommended = Column(Boolean, default=False)
    retraining_reason = Column(Text, nullable=True)

    call = relationship("Call", back_populates="feedback_notes")
