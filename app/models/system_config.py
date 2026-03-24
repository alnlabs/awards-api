# app/models/system_config.py

import sqlalchemy as sa
from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from app.models.base import Base

class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String, nullable=False, default="My Company")
    company_logo = Column(String, nullable=True)
    setup_complete = Column(sa.Boolean, nullable=False, default=False)
    
    # Store dynamic feature flags or other settings
    settings = Column(JSON, nullable=False, default={})

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
