from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.models.base import Base


class PanelReview(Base):
    __tablename__ = "panel_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    panel_assignment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("panel_assignments.id", ondelete="CASCADE"),
        nullable=False
    )

    panel_member_id = Column(
        UUID(as_uuid=True),
        ForeignKey("panel_members.id", ondelete="CASCADE"),
        nullable=False
    )

    panel_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("panel_tasks.id", ondelete="CASCADE"),
        nullable=False
    )

    score = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "panel_assignment_id",
            "panel_member_id",
            "panel_task_id",
            name="uq_unique_task_review"
        ),
    )

    # =====================
    # Relationships
    # =====================

    panel_assignment = relationship(
        "PanelAssignment",
        back_populates="reviews"
    )

    panel_member = relationship("PanelMember")

    panel_task = relationship("PanelTask")