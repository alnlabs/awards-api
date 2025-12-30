# Employee Awards API - Test Suite

This directory contains unit and integration tests for the Employee Awards API.

## ⚠️ IMPORTANT: Tests Run Only in Docker

**All tests must be run inside Docker containers.** Tests are not designed to run locally. Use `./test.sh` commands to execute tests.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── test_security.py         # Security utilities tests (password hashing, JWT)
├── test_response.py         # Response utility tests
├── test_auth.py            # Authentication endpoint tests
├── test_users.py           # User CRUD endpoint tests
├── test_config.py          # Configuration tests
└── test_health.py          # Health check endpoint tests
```

## Running Tests

**All tests must be run inside Docker containers using the scripts below.**

### Run all tests
```bash
./test.sh all
```

### Run tests with coverage
```bash
./test.sh coverage
```

### Run only unit tests
```bash
./test.sh unit
```

### Run only integration tests
```bash
./test.sh integration
```

### Run tests directly inside Docker container
If you need to run tests with custom options, you can shell into the container first:

```bash
# Open shell in container
./test.sh shell

# Then inside the container:
pytest tests/ -v
pytest tests/ -v --cov=app --cov-report=term-missing
pytest tests/test_auth.py -v
pytest tests/test_auth.py::TestAuthLogin::test_login_success -v
```

## Test Database

**Important**: Tests run inside Docker containers and use the database from `docker-compose.dev.yml` by default.

The codebase uses PostgreSQL-specific types (UUID, JSONB), so tests automatically connect to the PostgreSQL database container when run via `./test.sh all`.

You don't need to configure a test database separately - the Docker setup handles this automatically.

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests (isolated, no database)
- `@pytest.mark.integration` - Integration tests (with database)
- `@pytest.mark.auth` - Authentication-related tests
- `@pytest.mark.users` - User management tests
- `@pytest.mark.cycles` - Cycle management tests
- `@pytest.mark.forms` - Form management tests
- `@pytest.mark.nominations` - Nomination tests
- `@pytest.mark.awards` - Award tests

## Test Fixtures

### Database Fixtures
- `db_session` - Fresh database session for each test
- `client` - FastAPI TestClient with database override

### User Fixtures
- `test_user` - Generic test user (MANAGER role)
- `test_hr_user` - HR user with security questions
- `test_manager_user` - Manager user with security questions
- `test_employee_user` - Employee user
- `test_panel_user` - Panel user

### Authentication Fixtures
- `auth_token_hr` - JWT token for HR user
- `auth_token_manager` - JWT token for manager user
- `auth_token_employee` - JWT token for employee user
- `auth_token_panel` - JWT token for panel user
- `auth_headers_hr` - Authorization headers for HR user
- `auth_headers_manager` - Authorization headers for manager user
- `auth_headers_employee` - Authorization headers for employee user
- `auth_headers_panel` - Authorization headers for panel user

## Writing New Tests

1. Create a new test file following the naming pattern `test_*.py`
2. Import necessary fixtures from `conftest.py`
3. Use appropriate markers to categorize tests
4. Follow the existing test structure and naming conventions

Example:
```python
import pytest
from fastapi import status

@pytest.mark.integration
class TestMyFeature:
    def test_feature_success(self, client, auth_headers_hr):
        response = client.get("/api/v1/my-endpoint", headers=auth_headers_hr)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
```

## Coverage Goals

- Unit tests: Test individual functions and utilities in isolation
- Integration tests: Test API endpoints with database interactions
- Target coverage: 80%+ for core modules

## Notes

- Tests run with isolated databases (fresh DB for each test)
- All tests clean up after themselves
- Authentication is mocked using JWT tokens generated in fixtures
- Database operations use transactions that are rolled back after each test

