import pytest


@pytest.mark.unit
@pytest.mark.integration
class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

