from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole, SecurityQuestion


# ==========================================
# ADMIN CONFIG (ONLY ONE USER)
# ==========================================

ADMIN_EMAIL = "admin@company.com"
ADMIN_PASSWORD = "ChangeMe123"

SECURITY_QUESTIONS = [
    {
        "question": "What was the name of your first school?",
        "answer": "ABC School",
    },
    {
        "question": "What is your favorite food?",
        "answer": "Biryani",
    },
    {
        "question": "What city were you born in?",
        "answer": "Hyderabad",
    },
]


# ==========================================
# SEED LOGIC
# ==========================================

def run():
    db: Session = SessionLocal()
    try:
        print("🌱 Seeding database (HR admin only)...")

        existing_admin = (
            db.query(User)
            .filter(User.role == UserRole.HR)
            .first()
        )

        if existing_admin:
            print("ℹ️  HR admin already exists, skipping seed")
            print(f"   Email: {existing_admin.email}")
            return

        admin = User(
            name="System Admin",
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            role=UserRole.HR,
            is_active=True,
            created_at=datetime.utcnow(),
        )

        db.add(admin)
        db.flush()  # get admin.id

        # exactly 3 security questions (required by backend)
        for q in SECURITY_QUESTIONS:
            db.add(
                SecurityQuestion(
                    user_id=admin.id,
                    question=q["question"],
                    answer_hash=hash_password(q["answer"]),
                )
            )

        db.commit()

        print("✅ HR admin created successfully")
        print("")
        print("🔐 LOGIN DETAILS")
        print("----------------------------")
        print(f"Email    : {ADMIN_EMAIL}")
        print(f"Password : {ADMIN_PASSWORD}")
        print("----------------------------")

    finally:
        db.close()


if __name__ == "__main__":
    run()