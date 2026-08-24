from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, HttpUrl, Field


class MonitoredPageCreate(BaseModel):
    url: HttpUrl
    page_type: str = Field(default="custom")
    name: str | None = None
    check_frequency: str = Field(default="daily")


class MonitoredPageUpdate(BaseModel):
    monitoring_enabled: bool | None = None
    check_frequency: str | None = None
    name: str | None = None


class MonitoredPageOut(BaseModel):
    id: UUID
    url: str
    page_type: str
    name: str | None
    monitoring_enabled: bool
    check_frequency: str
    last_checked_at: datetime | None
    last_changed_at: datetime | None
    last_status_code: str | None

    model_config = ConfigDict(from_attributes=True)
