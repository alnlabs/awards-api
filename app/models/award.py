from uuid import uuid4
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Award(Base):
    __tablename__ = "awards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    cycle_id = Column(UUID(as_uuid=True), ForeignKey("cycles.id"), nullable=False)
    nomination_id = Column(UUID(as_uuid=True), ForeignKey("nominations.id"), nullable=False)
    winner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    award_type = Column(String(100), nullable=True)  # e.g., "Employee of the Quarter"
    rank = Column(Integer, nullable=True)  # 1st, 2nd, 3rd place
    comment = Column(String(1000), nullable=True)  # HR's announcement comment for the winner

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    finalized_at = Column(DateTime, nullable=True)

    cycle = relationship("Cycle", back_populates="awards")
    winner = relationship("User", foreign_keys=[winner_id])
    nomination = relationship("Nomination", foreign_keys=[nomination_id])
