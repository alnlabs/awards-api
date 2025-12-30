EMPLOYEE AWARDS API
FULL IMPLEMENTATION DOCUMENTATION

==================================================

1. PURPOSE

The Employee Awards API is an internal backend system built to manage the complete lifecycle of quarterly employee awards.

The system allows:

- Managers to nominate employees
- HR to define criteria, manage cycles, review nominations, and declare winners
- Panel members to evaluate nominees
- Employees to view award results

The API is secure, role-based, extensible, and designed for long-term internal use.

---

2. TECHNOLOGY STACK

Backend Framework:
FastAPI

Authentication:
JWT (OAuth2 Bearer Token)

Database:
PostgreSQL

ORM:
SQLAlchemy

Database Migrations:
Alembic

Containerization:
Docker (Development only)

Environment:
DEV-first (Production later)

---

3. API VERSIONING STRATEGY

The API uses versioning to allow future upgrades without breaking existing clients.

Key Rule:

- /api/v1 is treated as a COMMON LEVEL

Rules:

- /api/v1 is defined only once
- No core module knows about /api/v1
- No feature route hardcodes /api/v1
- Versioning is centralized

Single source of truth:
app/api/v1/api.py

Mounting:
main.py includes the v1 router

This design allows future versions like /api/v2 without changing core logic.

---

4. STANDARD API RESPONSE FORMAT

All APIs strictly follow a unified response contract.

SUCCESS RESPONSE:
status: success
message: Human-readable success message
error: null
data: payload or null

FAILURE RESPONSE:
status: failure
message: Human-readable failure message
error: error description
data: null

Rules:

- No API returns raw data
- No ad-hoc responses
- All responses use common response utility

---

5. AUTHENTICATION & AUTHORIZATION

Authentication is JWT-based and stateless.

OAuth2 Bearer Token is used.

Each protected request must include:
Authorization: Bearer <access_token>

---

6. USER ROLES

HR:

- Full system access
- Configure criteria
- Manage cycles
- Assign panels
- Finalize awards

MANAGER:

- Nominate employees
- View nomination history

EMPLOYEE:

- View awards
- View winners

PANEL:

- Review nominations
- Provide scores and comments

---

7. ROLE-BASED ACCESS CONTROL (RBAC)

RBAC is enforced using reusable dependencies.

Rules:

- Authentication mandatory
- Authorization explicit
- Role logic centralized
- No duplicated checks

---

8. API MODULES OVERVIEW

Auth Module:
Base Path: /api/v1/auth

Users Module:
Base Path: /api/v1/users

Criteria (Meta-Form) Module:
Base Path: /api/v1/forms

Nomination Module:
Base Path: /api/v1/nominations

Awards Module:
Base Path: /api/v1/awards

---

9. AUTHENTICATION APIS

REGISTER USER
POST /api/v1/auth/register

- Register user
- Capture exactly 3 security questions

LOGIN
POST /api/v1/auth/login

- Authenticate user
- Issue JWT token

CURRENT USER
GET /api/v1/auth/me

- Fetch logged-in user details

FORGOT PASSWORD
POST /api/v1/auth/forgot-password

- Verify security questions

RESET PASSWORD
POST /api/v1/auth/reset-password

- Update password

---

10. CRITERIA SYSTEM (META-FORM ENGINE)

Criteria are implemented as a dynamic form engine.

Key points:

- HR defines form fields
- Managers submit answers
- No DB schema changes required

Supported field types:
Text
Textarea
Number
Select
Multi-select
Radio
Checkbox
Rating
Date
Boolean
File

---

11. NOMINATION WORKFLOW

Nomination lifecycle:

DRAFT
→ SUBMITTED
→ HR_REVIEW
→ PANEL_REVIEW
→ FINALIZED

Rules:

- Nomination only during open cycle
- One nomination per employee per cycle
- Answers stored as JSON
- HR controls final status

---

12. PANEL REVIEW PROCESS

HR creates Panel 1 and Panel 2.

Panel members:

- Review assigned nominations
- Give score (1–5)
- Add comments

HR reviews aggregated scores.

---

13. AWARD FINALIZATION

HR finalizes winners.

After finalization:

- Winners announced
- Award history published
- Employees can view results

---

14. DATABASE DESIGN PRINCIPLES

- UUID primary keys
- Soft deletes using is_active
- JSONB for dynamic data
- Strong foreign keys
- Audit-friendly timestamps

---

15. SECURITY CONSIDERATIONS

- Passwords hashed with bcrypt
- Security answers hashed
- JWT expiry enforced
- Inactive users blocked
- No sensitive data exposed

---

16. DEVELOPMENT WORKFLOW

Start DEV:
./docker.sh start

Stop DEV:
./docker.sh stop

Reset DEV (DB wipe):
./docker.sh reset

---

17. FUTURE ENHANCEMENTS

- Refresh tokens
- Audit logs
- Notifications
- Dashboards
- Reports
- Production deployment

==================================================
