from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import require_role
from app.core.response import success_response, failure_response
from app.models.user import User, UserRole
from app.models.form import Form, FormField
from app.models.cycle import Cycle, CycleStatus
from app.schemas.forms import FormCreate, FormResponse, FormListResponse

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_form(
    payload: FormCreate,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    # Verify cycle exists
    cycle = db.get(Cycle, payload.cycle_id)
    if not cycle:
        failure_response(
            message="Form creation failed",
            error="Cycle not found",
            status_code=404
        )

    # Check for duplicate form name in cycle
    existing = db.query(Form).filter(
        Form.cycle_id == payload.cycle_id,
        Form.name == payload.name,
        Form.is_active == True
    ).first()
    if existing:
        failure_response(
            message="Form creation failed",
            error="Form with this name already exists for this cycle",
            status_code=400
        )

    # Validate field_keys are unique
    field_keys = [f.field_key for f in payload.fields]
    if len(field_keys) != len(set(field_keys)):
        failure_response(
            message="Form creation failed",
            error="Field keys must be unique",
            status_code=400
        )

    form = Form(
        name=payload.name,
        description=payload.description,
        cycle_id=payload.cycle_id
    )

    db.add(form)
    db.flush()  # Get form.id

    # Create form fields
    for idx, field_data in enumerate(payload.fields):
        form_field = FormField(
            form_id=form.id,
            label=field_data.label,
            field_key=field_data.field_key,
            field_type=field_data.field_type,
            is_required=field_data.is_required,
            order_index=field_data.order_index if field_data.order_index > 0 else idx,
            options=field_data.options,
            ui_schema=field_data.ui_schema,
            validation=field_data.validation
        )
        db.add(form_field)

    db.commit()
    db.refresh(form)

    # Load fields for response
    form.fields  # Trigger lazy load

    return success_response(
        message="Form created successfully",
        data={
            "id": str(form.id),
            "name": form.name,
            "cycle_id": str(form.cycle_id),
            "fields_count": len(form.fields)
        }
    )


@router.get("", response_model=dict)
def list_forms(
    cycle_id: UUID = None,
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(require_role(UserRole.HR, UserRole.MANAGER, UserRole.EMPLOYEE, UserRole.PANEL)),
    db: Session = Depends(get_db)
):
    query = db.query(Form).filter(Form.is_active == True)

    if cycle_id:
        query = query.filter(Form.cycle_id == cycle_id)

    forms = query.order_by(Form.created_at.desc()).offset(skip).limit(limit).all()

    return success_response(
        message="Forms fetched successfully",
        data=[
            {
                "id": str(f.id),
                "name": f.name,
                "description": f.description,
                "cycle_id": str(f.cycle_id),
                "is_active": f.is_active,
                "created_at": f.created_at.isoformat()
            }
            for f in forms
        ]
    )


@router.get("/{form_id}", response_model=dict)
def get_form(
    form_id: UUID,
    user: User = Depends(require_role(UserRole.HR, UserRole.MANAGER, UserRole.EMPLOYEE, UserRole.PANEL)),
    db: Session = Depends(get_db)
):
    form = db.get(Form, form_id)

    if not form or not form.is_active:
        failure_response(
            message="Form not found",
            error="Form does not exist",
            status_code=404
        )

    # Load fields
    fields = db.query(FormField).filter(
        FormField.form_id == form.id
    ).order_by(FormField.order_index).all()

    return success_response(
        message="Form fetched successfully",
        data={
            "id": str(form.id),
            "name": form.name,
            "description": form.description,
            "cycle_id": str(form.cycle_id),
            "is_active": form.is_active,
            "created_at": form.created_at.isoformat(),
            "fields": [
                {
                    "id": str(f.id),
                    "label": f.label,
                    "field_key": f.field_key,
                    "field_type": f.field_type,
                    "is_required": f.is_required,
                    "order_index": f.order_index,
                    "options": f.options,
                    "ui_schema": f.ui_schema,
                    "validation": f.validation
                }
                for f in fields
            ]
        }
    )


@router.get("/cycle/{cycle_id}/render", response_model=dict)
def render_form(
    cycle_id: UUID,
    user: User = Depends(require_role(UserRole.MANAGER, UserRole.HR)),
    db: Session = Depends(get_db)
):
    # Verify cycle exists and is open
    cycle = db.get(Cycle, cycle_id)
    if not cycle:
        failure_response(
            message="Cycle not found",
            error="Cycle does not exist",
            status_code=404
        )

    if cycle.status != CycleStatus.OPEN:
        failure_response(
            message="Cycle not open",
            error=f"Cycle is {cycle.status.value}. Nominations can only be submitted when cycle is OPEN.",
            status_code=400
        )

    # Get active form for this cycle
    form = db.query(Form).filter(
        Form.cycle_id == cycle_id,
        Form.is_active == True
    ).first()

    if not form:
        failure_response(
            message="Form not found",
            error="No active form found for this cycle",
            status_code=404
        )

    # Load fields
    fields = db.query(FormField).filter(
        FormField.form_id == form.id
    ).order_by(FormField.order_index).all()

    return success_response(
        message="Form rendered successfully",
        data={
            "form_id": str(form.id),
            "form_name": form.name,
            "cycle_id": str(cycle_id),
            "cycle_name": cycle.name,
            "fields": [
                {
                    "id": str(f.id),
                    "label": f.label,
                    "field_key": f.field_key,
                    "field_type": f.field_type,
                    "is_required": f.is_required,
                    "order_index": f.order_index,
                    "options": f.options,
                    "ui_schema": f.ui_schema,
                    "validation": f.validation
                }
                for f in fields
            ]
        }
    )