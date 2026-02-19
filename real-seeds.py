#!/usr/bin/env python3
"""
Script to seed REAL baseline data (no mock/sample users):
- Ensure SUPER_ADMIN exists.
Intended for prod/staging-safe baseline seeding.
"""

import sys
from pathlib import Path

# Add the app directory to the path so imports work
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.core.seed import seed_admin_user
from app.models import *  # Import all models to avoid mapping errors


def main():
    """Run real baseline seeding operations."""
    print("🌱 Starting REAL database seeding (baseline only)...")

    db = SessionLocal()
    try:
        print("📝 Ensuring SUPER_ADMIN user exists...")
        admin_result = seed_admin_user(db)

        print("📊 Real seed summary:")
        if admin_result:
            status = "created" if admin_result["created"] else "skipped"
            print(
                f"  - SUPER_ADMIN {status}: {admin_result['email']} "
                f"(role={admin_result['role']})"
            )
        else:
            print("  - SUPER_ADMIN: no action taken (seed function returned None)")

        print("✅ Real seeding completed successfully!")

    except Exception as e:
        print(f"❌ Error during real seeding: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

