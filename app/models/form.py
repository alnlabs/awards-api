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
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base

class Form(Base):
    __tablename__ = "forms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    name = Column(String(150), nullable=False)
    description = Column(String(500), nullable=True)

    cycle_id = Column(UUID(as_uuid=True), ForeignKey("cycles.id"), nullable=False)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    cycle = relationship("Cycle", back_populates="forms")

    fields = relationship(
        "FormField",
        back_populates="form",
        cascade="all, delete-orphan",
        order_by="FormField.order_index"
    )

class FormField(Base):
    __tablename__ = "form_fields"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    form_id = Column(UUID(as_uuid=True), ForeignKey("forms.id", ondelete="CASCADE"))

    label = Column(String(255), nullable=False)
    field_key = Column(String(100), nullable=False)

    field_type = Column(String(50), nullable=False)  # TEXT, SELECT, RATING, etc.
    is_required = Column(Boolean, default=False)

    order_index = Column(Integer, default=0)

    options = Column(JSONB, nullable=True)      # dropdown, radio, checkbox
    ui_schema = Column(JSONB, nullable=True)    # UI rendering hints
    validation = Column(JSONB, nullable=True)   # min/max/regex/etc

    form = relationship("Form", back_populates="fields")