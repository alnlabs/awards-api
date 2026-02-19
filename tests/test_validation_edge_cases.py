import pytest
from fastapi import status
import io
import json

@pytest.mark.validation
@pytest.mark.integration
class TestValidationEdgeCases:
    """Tests for API validation edge cases"""

    def test_create_user_invalid_role(self, client, auth_headers_hr):
        """Test creating user with invalid role"""
        payload = {
            "name": "Invalid Role User",
            "email": "invalidrole@example.com",
            "password": "password123",
            "role": "NOT_A_ROLE",
            "security_questions": [
                {"question": "Q1", "answer": "A1"},
                {"question": "Q2", "answer": "A2"},
                {"question": "Q3", "answer": "A3"}
            ]
        }
        response = client.post("/api/v1/users", json=payload, headers=auth_headers_hr)
        assert response.status_code == 400
        assert "invalid role" in response.json()["error"].lower()

    def test_create_user_missing_security_questions(self, client, auth_headers_hr):
        """Test creating user with insufficient security questions"""
        payload = {
            "name": "No SQ User",
            "email": "nosq@example.com",
            "password": "password123",
            "role": "EMPLOYEE",
            "security_questions": [
                {"question": "Q1", "answer": "A1"}
            ]
        }
        response = client.post("/api/v1/users", json=payload, headers=auth_headers_hr)
        assert response.status_code == 422
        # FastAPI/Pydantic errors usually contain "security_questions" in the loc
        assert "security_questions" in str(response.json())

    def test_bulk_upload_malformed_json(self, client, auth_headers_hr):
        """Test bulk upload with malformed JSON"""
        content = b"invalid json content"
        files = {"file": ("users.json", content, "application/json")}
        response = client.post("/api/v1/users/bulk-upload", files=files, headers=auth_headers_hr)
        assert response.status_code == 400
        assert "bulk upload failed" in response.json()["message"].lower()

    def test_bulk_upload_duplicate_email(self, client, auth_headers_hr, test_user):
        """Test bulk upload with a duplicate email record"""
        records = [
            {
                "name": "Bulk Duplicate",
                "email": test_user.email,
                "password": "password123",
                "role": "EMPLOYEE",
                "security_questions": [
                    {"question": "Q1", "answer": "A1"},
                    {"question": "Q2", "answer": "A2"},
                    {"question": "Q3", "answer": "A3"}
                ]
            }
        ]
        files = {"file": ("users.json", json.dumps(records), "application/json")}
        response = client.post("/api/v1/users/bulk-upload", files=files, headers=auth_headers_hr)
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["created"] == 0
        assert len(data["data"]["failed"]) == 1
        assert "already registered" in data["data"]["failed"][0]["error"].lower()

    def test_bulk_upload_invalid_role_record(self, client, auth_headers_hr):
        """Test bulk upload with a record having an invalid role"""
        records = [
            {
                "name": "Invalid Role Bulk",
                "email": "invalidbulk@example.com",
                "password": "password123",
                "role": "SUPER_SUPER_ADMIN",
                "security_questions": [
                    {"question": "Q1", "answer": "A1"},
                    {"question": "Q2", "answer": "A2"},
                    {"question": "Q3", "answer": "A3"}
                ]
            }
        ]
        files = {"file": ("users.json", json.dumps(records), "application/json")}
        response = client.post("/api/v1/users/bulk-upload", files=files, headers=auth_headers_hr)
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["created"] == 0
        assert len(data["data"]["failed"]) == 1
        # Pydantic validation error or our custom ValueError
        assert "role" in str(data["data"]["failed"][0]["error"]).lower()

    def test_update_user_duplicate_employee_code(self, client, auth_headers_hr, test_user, test_manager_user, db_session):
        """Test updating a user with an already existing employee code"""
        # Set employee code for test_manager_user
        test_manager_user.employee_code = "UNIQUE_EMP_CODE"
        db_session.commit()

        payload = {"employee_code": "UNIQUE_EMP_CODE"}
        response = client.patch(
            f"/api/v1/users/{test_user.id}",
            json=payload,
            headers=auth_headers_hr
        )
        assert response.status_code == 400
        assert "employee code already exists" in response.json()["error"].lower()
