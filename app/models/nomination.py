from uuid import uuid4
from datetime import datetime

from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Nomination(Base):
    __tablename__ = "nominations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    cycle_id = Column(UUID(as_uuid=True), ForeignKey("cycles.id"), nullable=False)
    form_id = Column(UUID(as_uuid=True), ForeignKey("forms.id"), nullable=False)

    nominee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    nominated_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    status = Column(String(50), default="DRAFT")

    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ✅ Form answers (correct)
    answers = relationship(
        "FormAnswer",
        back_populates="nomination",
        cascade="all, delete-orphan"
    )

    # ✅ Panel assignments (NEW & CORRECT)
    panel_assignments = relationship(
        "PanelAssignment",
        back_populates="nomination",
        cascade="all, delete-orphan"
    )

    # =====================
    # Other relationships
    # =====================
    cycle = relationship("Cycle", back_populates="nominations")
    form = relationship("Form", foreign_keys=[form_id])
    nominee = relationship("User", foreign_keys=[nominee_id])
    nominated_by = relationship("User", foreign_keys=[nominated_by_id])