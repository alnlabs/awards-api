# app/models/bulk_job.py

from sqlalchemy import Column, String, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from app.core.database import Base

class BulkJob(Base):
    __tablename__ = "bulk_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String, nullable=False)  # upload | delete
    status = Column(String, default="queued")

    total = Column(Integer, default=0)
    processed = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)

    payload = Column(JSON, nullable=False)
    error_file = Column(String, nullable=True)

    created_by = Column(UUID, ForeignKey("users.id"))

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    cancelled_at = Column(DateTime(timezone=True), nullable=True)