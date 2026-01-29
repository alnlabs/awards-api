from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles

from app.api.v1.api import api_router
from app.core.exception_handlers import (
    http_exception_handler,
    validation_exception_handler
)
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import SessionLocal
from app.core.seed import seed_admin_user
from app.core.lifecycle import auto_close_expired_cycles

app = FastAPI(title="Employee Awards API - DEV")

# ---- CORS (allow local dev UI & docs) ----
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:4100",  # API docs / proxy
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        
        # Auto-close expired cycles on startup
        closed_count = auto_close_expired_cycles(db)
        if closed_count > 0:
            print(f"✅ {closed_count} expired cycle(s) auto-closed on startup")
    except Exception as e:
        print(f"⚠️  Warning: Could not seed admin user: {e}")
    finally:
        db.close()

# ---- Serve static files (profile images) ----
# Mount static files BEFORE API router to avoid conflicts
try:
    import os
    os.makedirs("app/static/profile_images", exist_ok=True)
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except Exception as e:
    print(f"⚠️  Warning: Could not mount static files: {e}")
    # Directory might not exist yet, it will be created on first upload

# ---- Mount v1 API ----
app.include_router(api_router)