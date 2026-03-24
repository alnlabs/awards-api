import argparse
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.award_type import AwardType
from app.models.cycle import Cycle, CycleStatus
from app.models.form import Form, FormField
from app.models.system_config import SystemConfig
from app.core.config import settings
from app.core.seed import seed_admin_user

def seed_initial_config(db: Session, company_name: str = None, admin_email: str = None, admin_password: str = None, security_answers: list = None):
    print(f"🌱 Starting Full Initial Configuration in {settings.APP_ENV} environment...")

    # 0. Seed System Configuration (Always runs)
    print("📝 Ensuring System Configuration exists...")
    config = db.query(SystemConfig).first()
    target_company = company_name or "Employee Awards Platform"
    
    if not config:
        config = SystemConfig(
            company_name=target_company,
            settings={
                "allow_peer_nominations": True,
                "max_nominations_per_manager": 5
            }
        )
        db.add(config)
        print(f"✅ Default system configuration seeded for: {target_company}")
    else:
        print(f"  - Updating company name to: {target_company}")
        config.company_name = target_company
    
    db.flush()

    # 1. Ensure SUPER_ADMIN exists (Always runs)
    print("📝 Ensuring SUPER_ADMIN user exists...")
    admin_result = seed_admin_user(
        db, 
        email=admin_email, 
        password=admin_password, 
        security_answers=security_answers
    )
    if admin_result:
        print(f"  - SUPER_ADMIN processed: {admin_result['email']}")

    # Check if we should seed baseline data (Awards, Cycles, Forms)
    if settings.APP_ENV == "prod":
        print("ℹ️  Skipping baseline data seeding (Awards, Cycles, Forms) in prod environment.")
        db.commit()
        return

    # 1. Seed Award Types
    award_types_data = [
        {"code": "EXCELLENCE", "label": "Excellence Award", "description": "For outstanding performance and achievements."},
        {"code": "PEER", "label": "Peer Recognition", "description": "Nominated by colleagues for teamwork and support."},
        {"code": "INNOVATION", "label": "Innovation Award", "description": "For creative solutions and process improvements."},
    ]
    
    award_types = {}
    for data in award_types_data:
        at = db.query(AwardType).filter(AwardType.code == data["code"]).first()
        if not at:
            at = AwardType(**data)
            db.add(at)
            db.flush()
            print(f"✅ Created Award Type: {data['label']}")
        award_types[data["code"]] = at

    # 2. Seed Initial Cycle
    current_year = datetime.now().year
    cycle_name = f"Launch Cycle {current_year}"
    existing_cycle = db.query(Cycle).filter(Cycle.name == cycle_name).first()
    
    if not existing_cycle:
        new_cycle = Cycle(
            name=cycle_name,
            description="Initial award cycle for system launch.",
            quarter=f"Q{(datetime.now().month-1)//3 + 1}",
            year=current_year,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status=CycleStatus.ACTIVE,
            award_type_id=award_types["EXCELLENCE"].id
        )
        db.add(new_cycle)
        db.flush()
        print(f"✅ Created Initial Cycle: {cycle_name}")

    # 3. Seed Default Nomination Form
    existing_form = db.query(Form).filter(Form.name == "Standard Nomination Form").first()
    if not existing_form:
        form = Form(
            name="Standard Nomination Form",
            description="General nomination form for excellence and peer awards.",
            category="GENERAL"
        )
        db.add(form)
        db.flush()
        
        fields = [
            {"label": "Summary of Achievement", "field_key": "achievement_summary", "field_type": "TEXTAREA", "is_required": True, "order_index": 1},
            {"label": "Collaboration Impact", "field_key": "collaboration", "field_type": "RATING", "is_required": True, "order_index": 2},
            {"label": "Supporting Documents", "field_key": "documents", "field_type": "FILE", "is_required": False, "order_index": 3},
        ]
        
        for f_data in fields:
            field = FormField(form_id=form.id, **f_data)
            db.add(field)
        
        print(f"✅ Created Standard Nomination Form")
    
    db.commit()


def run():
    parser = argparse.ArgumentParser(description="Initial system configuration and seeding.")
    parser.add_argument("--company", help="Company Name")
    parser.add_argument("--email", help="Admin Email")
    parser.add_argument("--password", help="Admin Password")
    parser.add_argument("--answers", nargs=3, help="Security question answers (3 required)")
    
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        seed_initial_config(
            db, 
            company_name=args.company,
            admin_email=args.email,
            admin_password=args.password,
            security_answers=args.answers
        )
    finally:
        db.close()

if __name__ == "__main__":
    run()
