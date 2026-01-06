from uuid import uuid4
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class AwardType(Base):
    __tablename__ = "award_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    code = Column(String(100), unique=True, nullable=False, index=True)
    label = Column(String(150), nullable=False)
    description = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


