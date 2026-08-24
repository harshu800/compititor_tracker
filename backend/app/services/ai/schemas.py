from typing import Literal
from pydantic import BaseModel, Field, field_validator

ChangeType = Literal[
    "pricing", "feature", "positioning", "product", "offer",
    "cta", "content", "messaging", "legal", "design", "other",
]
Importance = Literal["critical", "high", "medium", "low"]


class AIClassification(BaseModel):
    """Strict schema for LLM output. Note: `importance` here is CONTEXT
    from the AI, not the number used for alerting/sorting — the backend's
    deterministic impact_scoring module is the source of truth for that.
    This field is retained only to sanity-check against the backend score
    and surface a mismatch for review."""
    change_type: ChangeType
    importance: Importance
    summary: str = Field(max_length=400)
    what_changed: str = Field(max_length=800)
    why_it_matters: str = Field(max_length=800)
    recommended_action: str = Field(max_length=500)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("summary", "what_changed", "why_it_matters", "recommended_action")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("field must not be empty")
        return v.strip()
