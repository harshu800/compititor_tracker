from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, HttpUrl, Field


class CompetitorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    website_url: HttpUrl
    description: str | None = None
    industry: str | None = None


class CompetitorUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    industry: str | None = None
    status: str | None = None  # active | archived


class CompetitorOut(BaseModel):
    id: UUID
    name: str
    website_url: str
    description: str | None
    industry: str | None
    logo_url: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
