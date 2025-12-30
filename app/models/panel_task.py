from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

from app.models.base import Base


class PanelTask(Base):
    __tablename__ = "panel_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    panel_id = Column(UUID(as_uuid=True), ForeignKey("panels.id"), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    max_score = Column(Integer, nullable=False, default=5)
    order_index = Column(Integer, nullable=False, default=0)
    is_required = Column(Boolean, default=True)