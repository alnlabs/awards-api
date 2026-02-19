from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole, SecurityQuestion


SAMPLE_USERS = [
    {
        "name": "HR Admin",
        "email": "hr.admin@example.com",
        "password": "HrAdmin123",
        "role": UserRole.HR,
    },
    {
        "name": "Line Manager",
        "email": "manager@example.com",
        "password": "Manager123",
        "role": UserRole.MANAGER,
    },
    {
        "name": "Panel Member",
        "email": "panel@example.com",
        "password": "Panel123",
        "role": UserRole.PANEL,
    },
    {
        "name": "Employee One",
        "email": "employee1@example.com",
        "password": "Employee123",
        "role": UserRole.EMPLOYEE,
    },
    {
        "name": "Employee Two",
        "email": "employee2@example.com",
        "password": "Employee123",
        "role": UserRole.EMPLOYEE,
    },
]


DEFAULT_SECURITY_QUESTIONS = [
    {
        "question": "What was the name of your first school?",
        "answer": "SampleSchool",
    },
    {
        "question": "What is your favorite food?",
        "answer": "Pizza",
    },
    {
        "question": "What city were you born in?",
        "answer": "SampleCity",
    },
]


def _ensure_user(db: Session, name: str, email: str, password: str, role: UserRole) -> bool:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"ℹ️  User already exists, skipping: {email}")
        return False

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.flush()

    # exactly 3 security questions (required by backend)
    for q in DEFAULT_SECURITY_QUESTIONS:
        db.add(
            SecurityQuestion(
                user_id=user.id,
                question=q["question"],
                answer_hash=hash_password(q["answer"]),
            )
        )

    return True


def run() -> dict:
    """Seed realistic sample users for all roles (HR, MANAGER, EMPLOYEE, PANEL)."""
    db: Session = SessionLocal()
    try:
        print("🌱 Seeding sample users (HR / MANAGER / EMPLOYEE / PANEL)...")

        created = 0
        skipped = 0
        for u in SAMPLE_USERS:
            if _ensure_user(
                db=db,
                name=u["name"],
                email=u["email"],
                password=u["password"],
                role=u["role"],
            ):
                created += 1
            else:
                skipped += 1

        db.commit()
        print(
            f"✅ Sample users seeded successfully (created={created}, skipped={skipped})"
        )
        return {"created": created, "skipped": skipped, "total": len(SAMPLE_USERS)}
    finally:
        db.close()


def seed_bulk_employees(count: int = 50) -> dict:
    """Seed a large number of employees for testing pagination/performance."""
    db: Session = SessionLocal()
    try:
        print(f"🌱 Generating {count} bulk employees...")
        created = 0
        skipped = 0

        for i in range(1, count + 1):
            email = f"employee.test{i}@example.com"
            name = f"Test Employee {i}"
            code = f"EMP{i:03d}"
            
            if _ensure_user(
                db=db,
                name=name,
                email=email,
                password="Employee123",
                role=UserRole.EMPLOYEE,
            ):
                # Optionally update employee code since _ensure_user doesn't take it as arg currently
                user = db.query(User).filter(User.email == email).first()
                user.employee_code = code
                created += 1
            else:
                skipped += 1

        db.commit()
        print(f"✅ Bulk seeding finished (created={created}, skipped={skipped})")
        return {"created": created, "skipped": skipped, "total": count}
    finally:
        db.close()


if __name__ == "__main__":
    run()
