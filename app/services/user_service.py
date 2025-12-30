from sqlalchemy.orm import Session
from app.models.user import User, UserRole, SecurityQuestion
from app.core.security import hash_password

def create_user_internal(db: Session, row: dict):
    if "security_questions" not in row or len(row["security_questions"]) != 3:
        raise ValueError("Exactly 3 security questions required")

    if not row.get("email"):
        raise ValueError("Email is required")

    if db.query(User).filter(User.email == row["email"]).first():
        raise ValueError("Email already exists")

    if row.get("employee_code") and db.query(User).filter(
        User.employee_code == row["employee_code"]
    ).first():
        raise ValueError("Employee code already exists")

    try:
        role = UserRole(row["role"].upper())
    except Exception:
        raise ValueError(f"Invalid role: {row.get('role')}")

    if role == UserRole.HR:
        raise ValueError("HR users cannot be bulk created")

    user = User(
        name=row["name"],
        email=row["email"],
        employee_code=row.get("employee_code"),
        role=role,
        password_hash=hash_password(row["password"]),
        is_active=True
    )

    db.add(user)
    db.flush()

    for q in row["security_questions"]:
        db.add(SecurityQuestion(
            user_id=user.id,
            question=q["question"],
            answer_hash=hash_password(q["answer"])
        ))

    db.commit()