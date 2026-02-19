#!/usr/bin/env python3
"""
Script to seed MOCK data for local/dev:
- SUPER_ADMIN
- Sample users for all roles (HR, MANAGER, EMPLOYEE, PANEL)
"""

import sys
from pathlib import Path

# Add the app directory to the path so imports work
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.core.seed import seed_admin_user
from app.models import *  # Import all models to avoid mapping errors
from app.seeds.sample_users import run as seed_sample_users, seed_bulk_employees


def main():
    """Run all mock seeding operations."""
    print("🌱 Starting MOCK database seeding...")

    db = SessionLocal()
    try:
        print("📝 Seeding SUPER_ADMIN user...")
        admin_result = seed_admin_user(db)

        print("📝 Seeding sample users (HR / MANAGER / EMPLOYEE / PANEL)...")
        sample_result = seed_sample_users()

        print("📊 Mock seed summary:")
        if admin_result:
            status = "created" if admin_result["created"] else "skipped"
            print(
                f"  - SUPER_ADMIN {status}: {admin_result['email']} "
                f"(role={admin_result['role']})"
            )
        if sample_result:
            print(
                f"  - Sample users: created={sample_result['created']}, "
                f"skipped={sample_result['skipped']}, total={sample_result['total']}"
            )

        print("📝 Seeding 50 bulk employees for pagination testing...")
        bulk_result = seed_bulk_employees(50)
        if bulk_result:
            print(
                f"  - Bulk employees: created={bulk_result['created']}, "
                f"skipped={bulk_result['skipped']}, total={bulk_result['total']}"
            )

        print("✅ Mock seeding completed successfully!")

    except Exception as e:
        print(f"❌ Error during mock seeding: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

