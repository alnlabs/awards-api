import pytest
from fastapi import status
from uuid import uuid4


@pytest.mark.users
@pytest.mark.integration
class TestUserCRUD:
    """Test user CRUD operations (HR only)"""

    def test_create_user_success(self, client, auth_headers_hr):
        """Test HR creating a user"""
        payload = {
            "name": "New Employee",
            "email": "newemployee@example.com",
            "password": "password123",
            "role": "EMPLOYEE",
            "employee_code": "EMP001",
            "security_questions": [
                {"question": "What is your pet's name?", "answer": "Fluffy"},
                {"question": "What city were you born in?", "answer": "Mumbai"},
                {"question": "What is your favorite color?", "answer": "Blue"}
            ]
        }

        response = client.post("/api/v1/users", json=payload, headers=auth_headers_hr)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["email"] == payload["email"]
        assert data["data"]["role"] == payload["role"]
        assert data["data"]["employee_code"] == payload["employee_code"]

    def test_create_user_unauthorized(self, client, auth_headers_manager):
        """Test non-HR user trying to create user"""
        payload = {
            "name": "New Employee",
            "email": "newemployee@example.com",
            "password": "password123",
            "role": "EMPLOYEE",
            "security_questions": [
                {"question": "Q1", "answer": "A1"},
                {"question": "Q2", "answer": "A2"},
                {"question": "Q3", "answer": "A3"}
            ]
        }

        response = client.post("/api/v1/users", json=payload, headers=auth_headers_manager)

        assert response.status_code == 403

    def test_create_user_duplicate_email(self, client, auth_headers_hr, test_user):
        """Test creating user with duplicate email"""
        payload = {
            "name": "Another User",
            "email": test_user.email,
            "password": "password123",
            "role": "EMPLOYEE",
            "security_questions": [
                {"question": "Q1", "answer": "A1"},
                {"question": "Q2", "answer": "A2"},
                {"question": "Q3", "answer": "A3"}
            ]
        }

        response = client.post("/api/v1/users", json=payload, headers=auth_headers_hr)

        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["error"].lower()

    def test_list_users_success(self, client, auth_headers_hr, test_user, test_manager_user):
        """Test HR listing users"""
        response = client.get("/api/v1/users", headers=auth_headers_hr)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 2

    def test_list_users_filter_by_role(self, client, auth_headers_hr, test_manager_user):
        """Test listing users filtered by role"""
        response = client.get(
            "/api/v1/users?role=MANAGER",
            headers=auth_headers_hr
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        for user in data["data"]:
            assert user["role"] == "MANAGER"

    def test_get_user_success(self, client, auth_headers_hr, test_user):
        """Test HR getting user details"""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers_hr
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == str(test_user.id)
        assert data["data"]["email"] == test_user.email

    def test_get_user_not_found(self, client, auth_headers_hr):
        """Test getting non-existent user"""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/users/{fake_id}",
            headers=auth_headers_hr
        )

        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "failure"

    def test_update_user_success(self, client, auth_headers_hr, test_user, db_session):
        """Test HR updating user"""
        payload = {
            "name": "Updated Name",
            "employee_code": "EMP999"
        }

        response = client.patch(
            f"/api/v1/users/{test_user.id}",
            json=payload,
            headers=auth_headers_hr
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["name"] == payload["name"]
        assert data["data"]["employee_code"] == payload["employee_code"]

    def test_update_user_role(self, client, auth_headers_hr, test_user):
        """Test HR updating user role"""
        payload = {"role": "EMPLOYEE"}

        response = client.patch(
            f"/api/v1/users/{test_user.id}",
            json=payload,
            headers=auth_headers_hr
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["role"] == "EMPLOYEE"

    def test_delete_user_success(self, client, auth_headers_hr, test_user):
        """Test HR deleting user (soft delete)"""
        response = client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers_hr
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["is_active"] is False

    def test_delete_user_self_prevention(self, client, auth_headers_hr, test_hr_user):
        """Test preventing HR from deleting own account"""
        response = client.delete(
            f"/api/v1/users/{test_hr_user.id}",
            headers=auth_headers_hr
        )

        assert response.status_code == 400
        data = response.json()
        assert "cannot delete your own account" in data["error"].lower()

    def test_get_current_user(self, client, auth_headers_manager, test_manager_user):
        """Test getting current user"""
        response = client.get("/api/v1/users/me", headers=auth_headers_manager)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == str(test_manager_user.id)
        assert data["data"]["email"] == test_manager_user.email

