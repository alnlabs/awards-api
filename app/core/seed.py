from sqlalchemy.orm import Session

from app.models.user import User, UserRole, SecurityQuestion
from app.core.security import hash_password


def seed_admin_user(db: Session):
    """
    Seed an admin user with HR role.
    Creates admin user if it doesn't exist.

    Default credentials:
    - Email: admin@company.com
    - Password: ChangeMe123
    - Role: HR

    Note: User should change password after first login.
    """
    admin_email = "admin@company.com"
    admin_password = "ChangeMe123"

    existing = db.query(User).filter(User.email == admin_email).first()
    if existing:
        print(f"ℹ️  Admin user already exists: {admin_email}")
        return

    admin = User(
        name="System Admin",
        email=admin_email,
        password_hash=hash_password(admin_password),
        role=UserRole.HR,
        is_active=True
    )

    db.add(admin)
    db.flush()  # Get admin.id for security questions

    # Add default security questions (required for password reset)
    security_questions = [
        SecurityQuestion(
            user_id=admin.id,
            question="What is your pet's name?",
            answer_hash=hash_password("Admin")
        ),
        SecurityQuestion(
            user_id=admin.id,
            question="What city were you born in?",
            answer_hash=hash_password("Default")
        ),
        SecurityQuestion(
            user_id=admin.id,
            question="What is your favorite color?",
            answer_hash=hash_password("Blue")
        ),
    ]

    for sq in security_questions:
        db.add(sq)

    db.commit()
    print(f"✅ Admin user created: {admin_email} (Password: {admin_password})")
    print("⚠️  Please change the password after first login!")