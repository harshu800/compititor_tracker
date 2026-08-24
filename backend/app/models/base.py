import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime
from app.models.column_types import GUID
from app.database import Base


class TimestampedBase(Base):
    __abstract__ = True
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
