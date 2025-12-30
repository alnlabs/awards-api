from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=True,           # DEV only (SQL logs)
    future=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base = declarative_base()