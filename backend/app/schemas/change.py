from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ChangeOut(BaseModel):
    id: UUID
    monitored_page_id: UUID
    change_type: str
    importance: str
    impact_score: float
    summary: str | None
    what_changed: str | None
    why_it_matters: str | None
    recommended_action: str | None
    ai_confidence: float | None
    diff_json: dict | None
    review_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChangeReviewUpdate(BaseModel):
    review_status: str  # unread | reviewed | important | ignored
