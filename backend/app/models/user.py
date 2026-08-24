from sqlalchemy import Column, String
from app.models.base import TimestampedBase


class User(TimestampedBase):
    __tablename__ = "users"
    clerk_user_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
