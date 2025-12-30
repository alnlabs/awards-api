from uuid import uuid4
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Integer,
    Text
)
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class PanelReview(Base):
    __tablename__ = "panel_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    nomination_id = Column(UUID(as_uuid=True), ForeignKey("nominations.id", ondelete="CASCADE"), nullable=False)
    panel_member_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    score = Column(Integer, nullable=False)  # 1-5
    comments = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
