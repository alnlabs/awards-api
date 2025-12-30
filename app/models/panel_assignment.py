from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4

from app.models.base import Base


class PanelAssignment(Base):
    __tablename__ = "panel_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    nomination_id = Column(UUID(as_uuid=True), ForeignKey("nominations.id"), nullable=False)
    panel_id = Column(UUID(as_uuid=True), ForeignKey("panels.id"), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    status = Column(String(20), nullable=False, default="PENDING")
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("nomination_id", "panel_id", name="uq_nomination_panel"),
    )