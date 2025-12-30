"""
Test configuration for Employee Awards API.

IMPORTANT: Tests are designed to run ONLY in Docker containers.
Do not run tests locally - use ./test.sh all instead.
"""
import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from uuid import uuid4

from app.main import app
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.base import Base
from app.models.user import User, UserRole, SecurityQuestion
from app.models.cycle import Cycle, CycleStatus
from app.models.form import Form, FormField
from app.models.nomination import Nomination
from app.models.award import Award
from app.models.panel_review import PanelReview
from app.core.security import hash_password, verify_password


# Pre-initialize bcrypt to avoid initialization errors during tests
# This is a workaround for bcrypt library compatibility issues
try:
    hash_password("init")
except (ValueError, AttributeError):
    # Ignore bcrypt initialization errors - they're library bugs, not our code
    pass


# Check if running in Docker (basic check)
RUNNING_IN_DOCKER = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'

# Warn if running locally (but don't fail - allow for development flexibility)
if not RUNNING_IN_DOCKER:
    import warnings
    warnings.warn(
               "⚠️  WARNING: Tests should be run in Docker containers using './test.sh all'. "
        "Running tests locally may fail due to missing dependencies or database configuration.",
        UserWarning
    )


# Test database URL - use PostgreSQL from docker-compose by default
# This ensures compatibility with JSONB and UUID types
# When running in Docker, we connect to the db service
# When running tests, we use the same database but create a test schema
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://awards_user:awards_pass@db:5432/awards_db"
)

# Create engine - always use PostgreSQL for tests to support JSONB
test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    echo=False,  # Disable SQL logging in tests
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test using PostgreSQL"""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.rollback()
        db.close()
        # Clean up tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def safe_hash_password(password: str) -> str:
    """Safely hash password, handling bcrypt initialization errors"""
    try:
        return hash_password(password)
    except (ValueError, AttributeError) as e:
        if "password cannot be longer than 72 bytes" in str(e) or "__about__" in str(e):
            # Pre-initialize by hashing a simple password first
            try:
                hash_password("init")
            except:
                pass
            return hash_password(password)
        raise


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        id=uuid4(),
        name="Test User",
        email="test@example.com",
        password_hash=safe_hash_password("testpass123"),
        role=UserRole.MANAGER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_hr_user(db_session):
    """Create a test HR user"""
    user = User(
        id=uuid4(),
        name="HR User",
        email="hr@example.com",
        password_hash=safe_hash_password("hrpass123"),
        role=UserRole.HR,
        is_active=True
    )
    db_session.add(user)

    # Add security questions
    questions = [
        SecurityQuestion(
            user_id=user.id,
            question="What is your pet's name?",
            answer_hash=safe_hash_password("Fluffy")
        ),
        SecurityQuestion(
            user_id=user.id,
            question="What city were you born in?",
            answer_hash=safe_hash_password("Mumbai")
        ),
        SecurityQuestion(
            user_id=user.id,
            question="What is your favorite color?",
            answer_hash=safe_hash_password("Blue")
        ),
    ]
    for q in questions:
        db_session.add(q)

    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_manager_user(db_session):
    """Create a test manager user"""
    user = User(
        id=uuid4(),
        name="Manager User",
        email="manager@example.com",
        password_hash=safe_hash_password("managerpass123"),
        role=UserRole.MANAGER,
        is_active=True
    )
    db_session.add(user)

    # Add security questions
    questions = [
        SecurityQuestion(
            user_id=user.id,
            question="What is your pet's name?",
            answer_hash=safe_hash_password("Fluffy")
        ),
        SecurityQuestion(
            user_id=user.id,
            question="What city were you born in?",
            answer_hash=safe_hash_password("Mumbai")
        ),
        SecurityQuestion(
            user_id=user.id,
            question="What is your favorite color?",
            answer_hash=safe_hash_password("Blue")
        ),
    ]
    for q in questions:
        db_session.add(q)

    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_employee_user(db_session):
    """Create a test employee user"""
    user = User(
        id=uuid4(),
        name="Employee User",
        email="employee@example.com",
        password_hash=safe_hash_password("employeepass123"),
        role=UserRole.EMPLOYEE,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_panel_user(db_session):
    """Create a test panel user"""
    user = User(
        id=uuid4(),
        name="Panel User",
        email="panel@example.com",
        password_hash=safe_hash_password("panelpass123"),
        role=UserRole.PANEL,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token_hr(test_hr_user):
    """Create JWT token for HR user"""
    return create_access_token({"sub": str(test_hr_user.id), "role": test_hr_user.role.value})


@pytest.fixture
def auth_token_manager(test_manager_user):
    """Create JWT token for manager user"""
    return create_access_token({"sub": str(test_manager_user.id), "role": test_manager_user.role.value})


@pytest.fixture
def auth_token_employee(test_employee_user):
    """Create JWT token for employee user"""
    return create_access_token({"sub": str(test_employee_user.id), "role": test_employee_user.role.value})


@pytest.fixture
def auth_token_panel(test_panel_user):
    """Create JWT token for panel user"""
    return create_access_token({"sub": str(test_panel_user.id), "role": test_panel_user.role.value})


@pytest.fixture
def auth_headers_hr(auth_token_hr):
    """Authorization headers for HR user"""
    return {"Authorization": f"Bearer {auth_token_hr}"}


@pytest.fixture
def auth_headers_manager(auth_token_manager):
    """Authorization headers for manager user"""
    return {"Authorization": f"Bearer {auth_token_manager}"}


@pytest.fixture
def auth_headers_employee(auth_token_employee):
    """Authorization headers for employee user"""
    return {"Authorization": f"Bearer {auth_token_employee}"}


@pytest.fixture
def auth_headers_panel(auth_token_panel):
    """Authorization headers for panel user"""
    return {"Authorization": f"Bearer {auth_token_panel}"}
