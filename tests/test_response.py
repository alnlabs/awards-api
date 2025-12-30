import pytest
from fastapi import HTTPException
from app.core.response import success_response, failure_response


@pytest.mark.unit
class TestSuccessResponse:
    """Test success response utility"""

    def test_success_response_with_data(self):
        """Test success response with data"""
        response = success_response(
            message="Operation successful",
            data={"id": "123", "name": "Test"}
        )

        assert response["status"] == "success"
        assert response["message"] == "Operation successful"
        assert response["error"] is None
        assert response["data"] == {"id": "123", "name": "Test"}

    def test_success_response_without_data(self):
        """Test success response without data"""
        response = success_response(message="Operation successful")

        assert response["status"] == "success"
        assert response["message"] == "Operation successful"
        assert response["error"] is None
        assert response["data"] is None

    def test_success_response_with_none_data(self):
        """Test success response with explicit None data"""
        response = success_response(
            message="Operation successful",
            data=None
        )

        assert response["status"] == "success"
        assert response["message"] == "Operation successful"
        assert response["error"] is None
        assert response["data"] is None


@pytest.mark.unit
class TestFailureResponse:
    """Test failure response utility"""

    def test_failure_response_raises_exception(self):
        """Test that failure_response raises HTTPException"""
        with pytest.raises(HTTPException) as exc_info:
            failure_response(
                message="Operation failed",
                error="Something went wrong",
                status_code=400
            )

        assert exc_info.value.status_code == 400
        assert isinstance(exc_info.value.detail, dict)
        assert exc_info.value.detail["status"] == "failure"
        assert exc_info.value.detail["message"] == "Operation failed"
        assert exc_info.value.detail["error"] == "Something went wrong"
        assert exc_info.value.detail["data"] is None

    def test_failure_response_default_status_code(self):
        """Test failure_response with default status code"""
        with pytest.raises(HTTPException) as exc_info:
            failure_response(
                message="Operation failed",
                error="Something went wrong"
            )

        assert exc_info.value.status_code == 400

    def test_failure_response_custom_status_code(self):
        """Test failure_response with custom status code"""
        with pytest.raises(HTTPException) as exc_info:
            failure_response(
                message="Not found",
                error="Resource not found",
                status_code=404
            )

        assert exc_info.value.status_code == 404

