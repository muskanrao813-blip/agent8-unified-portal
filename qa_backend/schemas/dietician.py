from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class DieticianResponse(BaseModel):
    id: UUID
    name: str
    external_id: Optional[str]
    created_at: datetime
    needs_admin_confirmation: bool

    class Config:
        from_attributes = True


class DieticianHistoryItem(BaseModel):
    call_id: UUID
    call_datetime: datetime
    overall_weighted_score: Optional[float]
    status: str


class DieticianTrendResponse(BaseModel):
    dietician: DieticianResponse
    last_10_calls: list[DieticianHistoryItem]
    average_score: Optional[float]
    call_count: int


class DieticianListItem(BaseModel):
    id: UUID
    name: str
    external_id: Optional[str]
    call_count: int
    avg_score: Optional[float]


class DieticianSummaryResponse(BaseModel):
    dietician_id: UUID
    name: str
    total_calls_analysed: int
    avg_overall_score: Optional[float]
    dimension_averages: dict[str, float]
    flag_counts: dict[str, int]
    retraining_recommended: bool
    trend: list[DieticianHistoryItem]
    peer_rank: int
    peer_total: int
    team_avg_score: float
    coaching_pointers: list[str]
