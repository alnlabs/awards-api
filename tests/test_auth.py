import pytest
from fastapi import status
from app.models.user import UserRole


@pytest.mark.auth
@pytest.mark.integration
class TestAuthRegistration:
    """Test user registration endpoint"""

    def test_register_user_success(self, client):
        """Test successful user registration"""
        payload = {
            "name": "New User",
            "email": "newuser@example.com",
            "password": "password123",
            "role": "MANAGER",
            "security_questions": [
                {"question": "What is your pet's name?", "answer": "Fluffy"},
                {"question": "What city were you born in?", "answer": "Mumbai"},
                {"question": "What is your favorite color?", "answer": "Blue"}
            ]
        }

        response = client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "User registered successfully"
        assert "user_id" in data["data"]

    def test_register_user_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        payload = {
            "name": "Another User",
            "email": test_user.email,
            "password": "password123",
            "role": "MANAGER",
            "security_questions": [
                {"question": "Q1", "answer": "A1"},
                {"question": "Q2", "answer": "A2"},
                {"question": "Q3", "answer": "A3"}
            ]
        }

        response = client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "failure"
        assert "already registered" in data["error"].lower()

    def test_register_user_invalid_role(self, client):
        """Test registration with invalid role"""
        payload = {
            "name": "New User",
            "email": "newuser@example.com",
            "password": "password123",
            "role": "INVALID_ROLE",
            "security_questions": [
                {"question": "Q1", "answer": "A1"},
                {"question": "Q2", "answer": "A2"},
                {"question": "Q3", "answer": "A3"}
            ]
        }

        response = client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "failure"

    def test_register_user_missing_security_questions(self, client):
        """Test registration with less than 3 security questions"""
        payload = {
            "name": "New User",
            "email": "newuser@example.com",
            "password": "password123",
            "role": "MANAGER",
            "security_questions": [
                {"question": "Q1", "answer": "A1"},
                {"question": "Q2", "answer": "A2"}
            ]
        }

        response = client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "failure"
        assert "3 security questions" in data["error"].lower()


@pytest.mark.auth
@pytest.mark.integration
class TestAuthLogin:
    """Test user login endpoint"""

    def test_login_success(self, client, test_manager_user):
        """Test successful login"""
        payload = {
            "email": test_manager_user.email,
            "password": "managerpass123"
        }

        response = client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    def test_login_invalid_email(self, client):
        """Test login with invalid email"""
        payload = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }

        response = client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "failure"
        assert "invalid" in data["error"].lower()

    def test_login_invalid_password(self, client, test_manager_user):
        """Test login with invalid password"""
        payload = {
            "email": test_manager_user.email,
            "password": "wrongpassword"
        }

        response = client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "failure"
        assert "invalid" in data["error"].lower()

    def test_login_inactive_user(self, client, db_session, test_manager_user):
        """Test login with inactive user"""
        test_manager_user.is_active = False
        db_session.commit()

        payload = {
            "email": test_manager_user.email,
            "password": "managerpass123"
        }

        response = client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == 403
        data = response.json()
        assert data["status"] == "failure"
        assert "inactive" in data["error"].lower()


@pytest.mark.auth
@pytest.mark.integration
class TestAuthMe:
    """Test get current user endpoint"""

    def test_me_success(self, client, auth_headers_manager, test_manager_user):
        """Test getting current user"""
        response = client.get("/api/v1/auth/me", headers=auth_headers_manager)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == str(test_manager_user.id)
        assert data["data"]["email"] == test_manager_user.email
        assert data["data"]["role"] == test_manager_user.role.value

    def test_me_unauthorized(self, client):
        """Test getting current user without token"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_me_invalid_token(self, client):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 401

