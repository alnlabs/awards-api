import enum
from uuid import uuid4
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Enum,
    Date,
    Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class CycleStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    FINALIZED = "FINALIZED"


class Cycle(Base):
    __tablename__ = "cycles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    name = Column(String(150), nullable=False)
    description = Column(String(500), nullable=True)
    quarter = Column(String(20), nullable=False)  # e.g., "Q1 2024"
    year = Column(Integer, nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(CycleStatus), default=CycleStatus.DRAFT, nullable=False)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    forms = relationship("Form", back_populates="cycle")
    nominations = relationship("Nomination", back_populates="cycle")
    awards = relationship("Award", back_populates="cycle")
