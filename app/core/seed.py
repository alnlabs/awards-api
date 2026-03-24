from sqlalchemy.orm import Session

from app.models.user import User, UserRole, SecurityQuestion
from app.core.security import hash_password


def seed_admin_user(db: Session, email: str = None, password: str = None, security_answers: list = None) -> dict:
    """
    Seed an admin user with SUPER_ADMIN role.
    Creates admin user if it doesn't exist, or updates it if it does.

    Default credentials (if not provided):
    - Email: admin@company.com
    - Password: ChangeMe123
    - Role: SUPER_ADMIN
    """
    admin_email = email or "admin@company.com"
    admin_password = password or "ChangeMe123"

    admin = db.query(User).filter(User.email == admin_email).first()
    
    if admin:
        print(f"ℹ️  Updating existing Admin user: {admin_email}")
        admin.is_active = True
        admin.role = UserRole.SUPER_ADMIN
        if password:
            admin.password_hash = hash_password(admin_password)
    else:
        print(f"📝 Creating new Admin user: {admin_email}")
        admin = User(
            name="System Admin",
            email=admin_email,
            password_hash=hash_password(admin_password),
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
        db.add(admin)
    
    db.flush()  # Ensure admin.id is available

    # Update or add security questions
    questions = [
        "What is your pet's name?",
        "What city were you born in?",
        "What is your favorite color?"
    ]
    
    # Default answers if not provided
    default_answers = ["Admin", "Default", "Blue"]
    answers = security_answers if security_answers and len(security_answers) == 3 else default_answers

    # Remove existing questions to start fresh (simplest for seed script)
    db.query(SecurityQuestion).filter(SecurityQuestion.user_id == admin.id).delete()
    
    for i, q_text in enumerate(questions):
        sq = SecurityQuestion(
            user_id=admin.id,
            question=q_text,
            answer_hash=hash_password(answers[i])
        )
        db.add(sq)

    db.commit()
    print(f"✅ Admin user processed: {admin_email}")
    if not email:
        print("⚠️  Using default credentials. Please change them!")

    return {
        "created": admin.id is not None,
        "email": admin_email,
        "role": UserRole.SUPER_ADMIN.value,
    }