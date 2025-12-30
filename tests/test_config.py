import pytest
import os
from app.core.config import settings


@pytest.mark.unit
class TestConfig:
    """Test configuration settings"""

    def test_settings_loaded(self):
        """Test that settings are loaded"""
        assert settings is not None
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'JWT_SECRET')
        assert hasattr(settings, 'JWT_ALGORITHM')
        assert hasattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES')

    def test_jwt_algorithm_default(self):
        """Test JWT algorithm default"""
        assert settings.JWT_ALGORITHM == "HS256"

    def test_token_expiry(self):
        """Test token expiry is configured (reads from .env file)"""
        # Token expiry comes from .env file, so just verify it's set
        # Default in code is 1440, but .env may override it
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert isinstance(settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)

