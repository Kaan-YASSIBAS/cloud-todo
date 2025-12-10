from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, DateTime, Text
from .db import Base

class Task(Base):
    __tablename__ = "tasks"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status      = Column(String(20), nullable=False, default="todo")
    due_date    = Column(DateTime, nullable=True)
    owner       = Column(String(150), index=True, nullable=False)
    created_at  = Column(DateTime, default=datetime.now(UTC))
    updated_at  = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
