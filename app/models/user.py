import enum
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Enum,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    HR = "HR"
    MANAGER = "MANAGER"
    EMPLOYEE = "EMPLOYEE"
    PANEL = "PANEL"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    employee_code = Column(String(50), unique=True, index=True, nullable=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)

    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)

    is_active = Column(Boolean, default=True)
    delete_requested_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    profile_image = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    security_questions = relationship(
        "SecurityQuestion",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    nominations_made = relationship(
        "Nomination",
        foreign_keys="Nomination.nominated_by_id",
        back_populates="nominated_by"
    )

    nominations_received = relationship(
        "Nomination",
        foreign_keys="Nomination.nominee_id",
        back_populates="nominee"
    )

class SecurityQuestion(Base):
    __tablename__ = "security_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    question = Column(String(255), nullable=False)
    answer_hash = Column(String(255), nullable=False)

    user = relationship("User", back_populates="security_questions")