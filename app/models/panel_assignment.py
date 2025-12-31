from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.models.base import Base


class PanelAssignment(Base):
    __tablename__ = "panel_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    nomination_id = Column(
        UUID(as_uuid=True),
        ForeignKey("nominations.id"),
        nullable=False
    )

    panel_id = Column(
        UUID(as_uuid=True),
        ForeignKey("panels.id"),
        nullable=False
    )

    assigned_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    status = Column(String(20), nullable=False, default="PENDING")
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    nomination = relationship(
        "Nomination",
        back_populates="panel_assignments"
    )

    reviews = relationship(
        "PanelReview",
        back_populates="panel_assignment",
        cascade="all, delete-orphan"
    )