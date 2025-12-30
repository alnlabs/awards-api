from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException

from app.api.v1.api import api_router
from app.core.exception_handlers import (
    http_exception_handler,
    validation_exception_handler
)
from app.core.database import SessionLocal
from app.core.seed import seed_admin_user

app = FastAPI(title="Employee Awards API - DEV")

# ---- Global exception handlers ----
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# ---- Startup event: Seed admin user ----
@app.on_event("startup")
def on_startup():
    """Seed admin user on application startup"""
    db = SessionLocal()
    try:
        seed_admin_user(db)
        print("✅ Admin user seeded (if not exists)")
    except Exception as e:
        print(f"⚠️  Warning: Could not seed admin user: {e}")
    finally:
        db.close()

# ---- Mount v1 API ----
app.include_router(api_router)