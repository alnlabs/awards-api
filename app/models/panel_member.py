from sqlalchemy import Column, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4

from app.models.base import Base


class PanelMember(Base):
    __tablename__ = "panel_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    panel_id = Column(UUID(as_uuid=True), ForeignKey("panels.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False)  # CHAIR | REVIEWER

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("panel_id", "user_id", name="uq_panel_member"),
    )