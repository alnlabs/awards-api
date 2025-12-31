from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import require_role
from app.core.response import success_response, failure_response
from app.models.user import User, UserRole
from app.models.form import Form, FormField
from app.schemas.forms import FormCreate

router = APIRouter()

# =========================================================
# CREATE CRITERIA
# =========================================================
@router.post("", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_form(
    payload: FormCreate,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(Form)
        .filter(Form.name == payload.name, Form.is_active == True)
        .first()
    )
    if existing:
        return failure_response(
            message="Criteria creation failed",
            error="Criteria with this name already exists",
            status_code=400,
        )

    field_keys = [f.field_key for f in payload.fields]
    if len(field_keys) != len(set(field_keys)):
        return failure_response(
            message="Criteria creation failed",
            error="Field keys must be unique",
            status_code=400,
        )

    form = Form(
        name=payload.name,
        description=payload.description,
        is_active=True,
    )

    db.add(form)
    db.flush()

    for idx, field in enumerate(payload.fields):
        db.add(
            FormField(
                form_id=form.id,
                label=field.label,
                field_key=field.field_key,
                field_type=field.field_type,
                is_required=field.is_required,
                order_index=idx,
                options=field.options,
                ui_schema=field.ui_schema,
                validation=field.validation,
            )
        )

    db.commit()
    db.refresh(form)

    return success_response(
        message="Criteria created successfully",
        data={"id": str(form.id)},
    )


# =========================================================
# ✅ UPDATE CRITERIA (EDIT)
# =========================================================
@router.put("/{form_id}", response_model=dict)
def update_form(
    form_id: UUID,
    payload: FormCreate,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    form = db.get(Form, form_id)

    if not form or not form.is_active:
        return failure_response(
            message="Criteria not found",
            error="Invalid criteria ID",
            status_code=404,
        )

    # Validate unique field keys
    field_keys = [f.field_key for f in payload.fields]
    if len(field_keys) != len(set(field_keys)):
        return failure_response(
            message="Criteria update failed",
            error="Field keys must be unique",
            status_code=400,
        )

    # Update main form
    form.name = payload.name
    form.description = payload.description

    # Remove old fields
    db.query(FormField).filter(FormField.form_id == form.id).delete()

    # Insert updated fields
    for idx, field in enumerate(payload.fields):
        db.add(
            FormField(
                form_id=form.id,
                label=field.label,
                field_key=field.field_key,
                field_type=field.field_type,
                is_required=field.is_required,
                order_index=idx,
                options=field.options,
                ui_schema=field.ui_schema,
                validation=field.validation,
            )
        )

    db.commit()

    return success_response(
        message="Criteria updated successfully",
        data={"id": str(form.id)},
    )


# =========================================================
# LIST CRITERIA
# =========================================================
@router.get("", response_model=dict)
def list_forms(
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(
        require_role(UserRole.HR, UserRole.MANAGER, UserRole.PANEL)
    ),
    db: Session = Depends(get_db),
):
    forms = (
        db.query(Form)
        .filter(Form.is_active == True)
        .order_by(Form.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []

    for form in forms:
        fields = (
            db.query(FormField)
            .filter(FormField.form_id == form.id)
            .order_by(FormField.order_index)
            .all()
        )

        result.append(
            {
                "id": str(form.id),
                "name": form.name,
                "description": form.description,
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
                        "validation": f.validation,
                    }
                    for f in fields
                ],
            }
        )

    return success_response(
        message="Criteria fetched successfully",
        data=result,
    )


# =========================================================
# ACTIVE CRITERIA (ORDER IMPORTANT)
# =========================================================
@router.get("/active", response_model=dict)
def render_active_criteria(
    user: User = Depends(
        require_role(UserRole.HR, UserRole.MANAGER, UserRole.PANEL)
    ),
    db: Session = Depends(get_db),
):
    form = (
        db.query(Form)
        .filter(Form.is_active == True)
        .order_by(Form.created_at.desc())
        .first()
    )

    if not form:
        return failure_response(
            message="No active criteria found",
            error="Create criteria first",
            status_code=404,
        )

    fields = (
        db.query(FormField)
        .filter(FormField.form_id == form.id)
        .order_by(FormField.order_index)
        .all()
    )

    return success_response(
        message="Criteria rendered successfully",
        data={
            "form_id": str(form.id),
            "form_name": form.name,
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
                    "validation": f.validation,
                }
                for f in fields
            ],
        },
    )


# =========================================================
# GET CRITERIA BY ID
# =========================================================
@router.get("/{form_id}", response_model=dict)
def get_form(
    form_id: UUID,
    user: User = Depends(
        require_role(UserRole.HR, UserRole.MANAGER, UserRole.PANEL)
    ),
    db: Session = Depends(get_db),
):
    form = db.get(Form, form_id)

    if not form or not form.is_active:
        return failure_response(
            message="Criteria not found",
            error="Criteria does not exist",
            status_code=404,
        )

    fields = (
        db.query(FormField)
        .filter(FormField.form_id == form.id)
        .order_by(FormField.order_index)
        .all()
    )

    return success_response(
        message="Criteria fetched successfully",
        data={
            "id": str(form.id),
            "name": form.name,
            "description": form.description,
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
                    "validation": f.validation,
                }
                for f in fields
            ],
        },
    )