from uuid import uuid4

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class FormAnswer(Base):
    __tablename__ = "form_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    nomination_id = Column(
        UUID(as_uuid=True),
        ForeignKey("nominations.id", ondelete="CASCADE"),
        nullable=False
    )

    field_key = Column(String(100), nullable=False)
    value = Column(JSONB, nullable=False)

    nomination = relationship("Nomination", back_populates="answers")