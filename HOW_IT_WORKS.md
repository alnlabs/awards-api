# How Employee Awards API Works

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Database Models & Relationships](#database-models--relationships)
4. [Complete Workflow](#complete-workflow)
5. [Request Flow](#request-flow)
6. [Key Features](#key-features)

---

## 🏗️ Architecture Overview

### Technology Stack
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT (OAuth2 Bearer Token)
- **Migrations**: Alembic
- **Containerization**: Docker

### Project Structure
```
employee-awards-api/
├── app/
│   ├── api/v1/          # API endpoints (routes)
│   ├── core/            # Core utilities (auth, security, database)
│   ├── models/          # Database models (SQLAlchemy)
│   ├── schemas/         # Pydantic schemas (request/response validation)
│   └── main.py          # FastAPI application entry point
├── alembic/             # Database migrations
└── docker/              # Docker configuration
```

---

## 🔐 Authentication & Authorization

### Authentication Flow

1. **User Registration** (`POST /api/v1/auth/register`)
   ```
   User → Provides: name, email, password, role, 3 security questions
   System → Creates user, hashes password & answers, stores in DB
   Response → Returns user_id
   ```

2. **Login** (`POST /api/v1/auth/login`)
   ```
   User → Provides: email, password
   System → Validates credentials, checks if user is active
   Response → Returns JWT access token
   ```

3. **Protected Endpoints**
   ```
   Request → Includes: Authorization: Bearer <token>
   System → Validates JWT, extracts user info, checks role
   Access → Granted/Denied based on role
   ```

### Role-Based Access Control (RBAC)

The system uses 4 roles with different permissions:

| Role | Permissions |
|------|------------|
| **HR** | Full system access - create cycles, forms, manage nominations, finalize awards |
| **MANAGER** | Create nominations, view own nomination history |
| **EMPLOYEE** | View award results and winners |
| **PANEL** | Review nominations, provide scores (1-5) and comments |

**Implementation**: `require_role()` dependency checks user role before allowing access.

---

## 🗄️ Database Models & Relationships

### Core Models

#### 1. **User** (`users` table)
```python
- id (UUID, PK)
- employee_code (String, unique)
- name, email (String)
- password_hash (String, bcrypt)
- role (Enum: HR, MANAGER, EMPLOYEE, PANEL)
- is_active (Boolean)
- created_at (DateTime)
```

#### 2. **Cycle** (`cycles` table)
Represents an award cycle (e.g., Q1 2024)
```python
- id (UUID, PK)
- name, description, quarter, year
- start_date, end_date (Date)
- status (Enum: DRAFT, OPEN, CLOSED, FINALIZED)
- is_active (Boolean)
```

#### 3. **Form** (`forms` table) + **FormField** (`form_fields` table)
Dynamic form engine for award criteria
```python
Form:
- id, name, description
- cycle_id (FK → cycles)

FormField:
- id, label, field_key, field_type
- is_required, order_index
- options, ui_schema, validation (JSONB)
```

#### 4. **Nomination** (`nominations` table)
```python
- id (UUID, PK)
- cycle_id (FK → cycles)
- form_id (FK → forms)
- nominee_id (FK → users)
- nominated_by_id (FK → users)
- status (String: DRAFT → SUBMITTED → HR_REVIEW → PANEL_REVIEW → FINALIZED)
- submitted_at, created_at, updated_at
```

#### 5. **FormAnswer** (`form_answers` table)
Stores nomination responses as JSONB
```python
- id
- nomination_id (FK → nominations)
- field_key (String)
- value (JSONB) - Flexible data storage
```

#### 6. **PanelReview** (`panel_reviews` table)
```python
- id
- nomination_id (FK → nominations)
- panel_member_id (FK → users)
- score (Integer: 1-5)
- comments (Text)
- created_at, updated_at
```

#### 7. **Award** (`awards` table)
```python
- id
- cycle_id (FK → cycles)
- nomination_id (FK → nominations)
- winner_id (FK → users)
- award_type, rank (Integer: 1st, 2nd, 3rd)
- finalized_at (DateTime)
```

### Relationships Diagram
```
Cycle (1) ────< (M) Form
  │
  ├───< (M) Nomination
  │      │
  │      ├───< (M) FormAnswer
  │      │
  │      └───< (M) PanelReview
  │
  └───< (M) Award

User (1) ────< (M) Nomination (as nominee)
User (1) ────< (M) Nomination (as nominator)
User (1) ────< (M) PanelReview (as panel member)
User (1) ────< (M) Award (as winner)
```

---

## 🔄 Complete Workflow

### Phase 1: Setup (HR Only)

#### 1.1 Create Award Cycle
```
HR → POST /api/v1/cycles
     {
       "name": "Q1 2024 Awards",
       "quarter": "Q1",
       "year": 2024,
       "start_date": "2024-01-01",
       "end_date": "2024-03-31",
       "status": "DRAFT"
     }
System → Creates cycle with status DRAFT
```

#### 1.2 Create Form (Award Criteria)
```
HR → POST /api/v1/forms
     {
       "name": "Employee of the Quarter",
       "cycle_id": "...",
       "fields": [
         {
           "label": "Performance Rating",
           "field_key": "performance",
           "field_type": "RATING",
           "is_required": true,
           "order_index": 1
         },
         {
           "label": "Achievements",
           "field_key": "achievements",
           "field_type": "TEXTAREA",
           "is_required": true,
           "order_index": 2
         }
       ]
     }
System → Creates form with dynamic fields (stored as FormField records)
```

#### 1.3 Open Cycle
```
HR → PATCH /api/v1/cycles/{cycle_id}
     { "status": "OPEN" }
System → Updates cycle status to OPEN
→ Now managers can submit nominations
```

---

### Phase 2: Nomination (Managers)

#### 2.1 Render Form for Nomination
```
Manager → GET /api/v1/forms/cycle/{cycle_id}/render
System → Returns form structure with all fields
         Validates cycle is OPEN
```

#### 2.2 Submit Nomination
```
Manager → POST /api/v1/nominations
          {
            "cycle_id": "...",
            "form_id": "...",
            "nominee_id": "...",
            "answers": [
              { "field_key": "performance", "value": 5 },
              { "field_key": "achievements", "value": "Led project..." }
            ],
            "status": "SUBMITTED"
          }

System → Validates:
  - Cycle is OPEN
  - Form belongs to cycle
  - Nominee exists and is active
  - One nomination per employee per cycle
  - All required fields answered
  - No invalid field keys

System → Creates:
  - Nomination record (status: SUBMITTED)
  - FormAnswer records for each answer (stored as JSONB)
```

**Draft Mode**: If status is "DRAFT", manager can save incomplete nominations and submit later.

---

### Phase 3: Review Process (HR + Panel)

#### 3.1 HR Reviews Nominations
```
HR → GET /api/v1/nominations?status=SUBMITTED
System → Returns all submitted nominations

HR → PATCH /api/v1/nominations/{nomination_id}/status
      { "status": "HR_REVIEW" }
System → Updates nomination status
```

#### 3.2 Panel Members Review
```
HR → PATCH /api/v1/nominations/{nomination_id}/status
      { "status": "PANEL_REVIEW" }

Panel Member → POST /api/v1/nominations/{nomination_id}/review
               {
                 "nomination_id": "...",
                 "score": 4,
                 "comments": "Strong performance..."
               }

System → Creates/updates PanelReview record
         Stores score (1-5) and comments
```

**Multiple Panel Members**: Each panel member can review the same nomination independently.

#### 3.3 HR Views Scores
```
HR → GET /api/v1/awards/cycle/{cycle_id}/nominations-with-scores
System → Returns nominations with:
  - Average score across all panel reviews
  - Review count
  - Sorted by average score (descending)
```

---

### Phase 4: Award Finalization (HR)

#### 4.1 Create Awards
```
HR → For each winner:
     POST /api/v1/awards
     {
       "cycle_id": "...",
       "nomination_id": "...",
       "winner_id": "...",
       "award_type": "Employee of the Quarter",
       "rank": 1
     }

System → Validates:
  - Nomination is FINALIZED
  - Winner matches nominee
  - Creates Award record
```

#### 4.2 Finalize Nominations
```
HR → PATCH /api/v1/nominations/{nomination_id}/status
      { "status": "FINALIZED" }
```

#### 4.3 Finalize Cycle
```
HR → POST /api/v1/awards/cycle/{cycle_id}/finalize
System →
  - Sets finalized_at timestamp on all awards
  - Updates cycle status to FINALIZED
  - Awards are now visible to all employees
```

---

### Phase 5: View Results (Employees)

```
Employee → GET /api/v1/awards/current
System → Returns all finalized awards for current cycle

Employee → GET /api/v1/awards/history
System → Returns all past awards
```

---

## 📡 Request Flow

### Example: Submit Nomination

```
1. Client Request
   POST /api/v1/nominations
   Headers: Authorization: Bearer <jwt_token>
   Body: { cycle_id, form_id, nominee_id, answers }

2. FastAPI Router
   app/api/v1/api.py → includes nominations.router
   app/api/v1/nominations.py → submit_nomination()

3. Authentication Middleware
   require_role(UserRole.MANAGER, UserRole.HR)
   ↓
   get_current_user() → Validates JWT token
   ↓
   Returns User object

4. Authorization Check
   require_role() → Verifies user.role is MANAGER or HR
   ↓
   Allows access

5. Business Logic
   submit_nomination():
     - Validates cycle exists and is OPEN
     - Validates form belongs to cycle
     - Validates nominee exists
     - Checks for duplicate nominations
     - Validates all required fields
     - Creates Nomination + FormAnswer records

6. Database Transaction
   db.add(nomination)
   db.commit()

7. Response
   success_response(message="...", data={...})
   ↓
   Returns: {
     "status": "success",
     "message": "Nomination submitted successfully",
     "error": null,
     "data": { "id": "...", "status": "SUBMITTED" }
   }
```

---

## 🎯 Key Features

### 1. Dynamic Form Engine
- **No hardcoded fields**: Forms are defined at runtime
- **JSONB storage**: Flexible field types (TEXT, RATING, SELECT, etc.)
- **Validation rules**: Stored as JSON, validated on submission

### 2. Standardized Response Format
All endpoints return consistent format:
```json
{
  "status": "success|failure",
  "message": "Human-readable message",
  "error": null | "error description",
  "data": payload | null
}
```

### 3. Workflow State Management
Nominations follow strict workflow:
```
DRAFT → SUBMITTED → HR_REVIEW → PANEL_REVIEW → FINALIZED
```
Status transitions are controlled and validated.

### 4. One Nomination Per Employee Per Cycle
System enforces business rule: Each employee can only have one active nomination per cycle.

### 5. Panel Scoring System
- Multiple panel members can review same nomination
- Scores aggregated (average calculated)
- Supports ranking and winner selection

### 6. Soft Deletes
- Models use `is_active` flag instead of hard deletes
- Preserves data integrity and audit trail

### 7. Security Features
- Passwords hashed with bcrypt
- Security question answers hashed
- JWT tokens with expiration
- Role-based access control
- Input validation via Pydantic schemas

---

## 🔄 Data Flow Example

### Complete Example: Q1 2024 Awards

```
1. HR Creates Cycle
   POST /api/v1/cycles → Cycle created (DRAFT)

2. HR Creates Form
   POST /api/v1/forms → Form + FormFields created

3. HR Opens Cycle
   PATCH /api/v1/cycles/{id} → status = OPEN

4. Manager Submits Nomination
   POST /api/v1/nominations →
     Nomination created (SUBMITTED)
     FormAnswers created (JSONB)

5. HR Reviews
   PATCH /api/v1/nominations/{id}/status → status = HR_REVIEW

6. Panel Reviews
   POST /api/v1/nominations/{id}/review →
     PanelReview created (score: 4, comments: "...")

   (Another panel member)
   POST /api/v1/nominations/{id}/review →
     PanelReview updated (score: 5, comments: "...")

7. HR Views Scores
   GET /api/v1/awards/cycle/{id}/nominations-with-scores
   → Returns: avg_score: 4.5, review_count: 2

8. HR Creates Award
   POST /api/v1/awards → Award created (rank: 1)

9. HR Finalizes Nomination
   PATCH /api/v1/nominations/{id}/status → status = FINALIZED

10. HR Finalizes Cycle
    POST /api/v1/awards/cycle/{id}/finalize →
      All awards finalized
      Cycle status = FINALIZED

11. Employees View Results
    GET /api/v1/awards/current → Returns all winners
```

---

## 🛡️ Security Layers

1. **Authentication**: JWT token validation on every request
2. **Authorization**: Role-based access control
3. **Input Validation**: Pydantic schemas validate all inputs
4. **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
5. **Password Security**: bcrypt hashing
6. **Data Integrity**: Foreign key constraints, transactions

---

## 📊 API Endpoints Summary

### Auth (`/api/v1/auth`)
- `POST /register` - User registration
- `POST /login` - Get JWT token
- `GET /me` - Current user info
- `POST /forgot-password` - Verify security questions
- `POST /reset-password` - Reset password

### Cycles (`/api/v1/cycles`)
- `POST /` - Create cycle (HR)
- `GET /` - List cycles
- `GET /{id}` - Get cycle details
- `PATCH /{id}` - Update cycle (HR)

### Forms (`/api/v1/forms`)
- `POST /` - Create form (HR)
- `GET /` - List forms
- `GET /{id}` - Get form details
- `GET /cycle/{cycle_id}/render` - Render form for nomination

### Nominations (`/api/v1/nominations`)
- `POST /` - Submit nomination (Manager)
- `GET /` - List nominations (HR/Panel)
- `GET /history` - Nomination history (Manager)
- `GET /{id}` - Get nomination details
- `PATCH /{id}/status` - Update status (HR)
- `POST /{id}/review` - Submit panel review (Panel)

### Awards (`/api/v1/awards`)
- `POST /` - Create award (HR)
- `GET /history` - Awards history
- `GET /current` - Current awards
- `GET /{id}` - Get award details
- `POST /cycle/{cycle_id}/finalize` - Finalize cycle (HR)
- `GET /cycle/{cycle_id}/nominations-with-scores` - View scores (HR)

### Users (`/api/v1/users`)
- `GET /me` - Current user
- `GET /` - List users (HR)
- `GET /{id}` - Get user (HR)
- `PATCH /{id}` - Update user (HR)

---

## 💡 Design Principles

1. **Separation of Concerns**: Models, schemas, and routes are separate
2. **DRY (Don't Repeat Yourself)**: Reusable dependencies and utilities
3. **Standardized Responses**: Consistent API response format
4. **Type Safety**: Pydantic schemas for validation
5. **Database Agnostic Logic**: Business logic in API layer, not models
6. **Versioning Ready**: `/api/v1` allows future `/api/v2` without breaking changes

---

This system provides a complete, secure, and flexible employee awards management platform with role-based access, dynamic forms, and a structured workflow from nomination to finalization.

