import pytest
from fastapi import status
from uuid import uuid4

from app.models.user import User, UserRole


@pytest.mark.users
@pytest.mark.integration
class TestUserBulkDelete:
    def test_bulk_delete_success_soft_deletes_non_hr_users(
        self,
        client,
        auth_headers_hr,
        db_session,
        test_employee_user,
        test_panel_user,
    ):
        payload = {"user_ids": [str(test_employee_user.id), str(test_panel_user.id)]}

        resp = client.post("/api/v1/users/bulk-delete", json=payload, headers=auth_headers_hr)

        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["deleted_count"] == 2

        db_session.refresh(test_employee_user)
        db_session.refresh(test_panel_user)
        assert test_employee_user.is_active is False
        assert test_panel_user.is_active is False

    def test_bulk_delete_skips_current_user_instead_of_failing(
        self,
        client,
        auth_headers_hr,
        db_session,
        test_hr_user,
        test_employee_user,
    ):
        payload = {"user_ids": [str(test_hr_user.id), str(test_employee_user.id)]}

        resp = client.post("/api/v1/users/bulk-delete", json=payload, headers=auth_headers_hr)

        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["deleted_count"] == 1
        assert str(test_hr_user.id) in body["data"]["skipped_self_ids"]

        db_session.refresh(test_hr_user)
        db_session.refresh(test_employee_user)
        assert test_hr_user.is_active is True
        assert test_employee_user.is_active is False

    def test_bulk_delete_skips_hr_targets(
        self,
        client,
        auth_headers_hr,
        db_session,
        test_employee_user,
    ):
        other_hr = User(
            id=uuid4(),
            name="Other HR",
            email="other-hr@example.com",
            password_hash="x",
            role=UserRole.HR,
            is_active=True,
        )
        db_session.add(other_hr)
        db_session.commit()
        db_session.refresh(other_hr)

        payload = {"user_ids": [str(other_hr.id), str(test_employee_user.id)]}
        resp = client.post("/api/v1/users/bulk-delete", json=payload, headers=auth_headers_hr)

        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["deleted_count"] == 1
        assert "skipped_admin_users" in body["data"]
        assert any(u["id"] == str(other_hr.id) for u in body["data"]["skipped_admin_users"])

        db_session.refresh(other_hr)
        db_session.refresh(test_employee_user)
        assert other_hr.is_active is True
        assert test_employee_user.is_active is False

    def test_bulk_delete_invalid_uuid_returns_400(self, client, auth_headers_hr):
        payload = {"user_ids": ["not-a-uuid"]}
        resp = client.post("/api/v1/users/bulk-delete", json=payload, headers=auth_headers_hr)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        body = resp.json()
        assert body["status"] == "failure"

    def test_bulk_delete_not_found_returns_404(self, client, auth_headers_hr):
        payload = {"user_ids": [str(uuid4())]}
        resp = client.post("/api/v1/users/bulk-delete", json=payload, headers=auth_headers_hr)
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        body = resp.json()
        assert body["status"] == "failure"

