from sqlalchemy import text
from app.core.database import engine


def check_db_connection():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))