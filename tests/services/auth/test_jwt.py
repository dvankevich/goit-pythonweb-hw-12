"""JWT token service tests."""

import pytest
from datetime import timedelta, datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from jose import jwt
from fastapi import HTTPException, status

from src.services.auth import (
    create_access_token,
    get_email_from_token,
)
from src.models import User, UserRole
from src.config.app_config import settings


async def test_create_access_token():
    """Test JWT token creation."""
    email = "test@example.com"
    token = create_access_token(email=email)
    
    assert isinstance(token, str)
    assert len(token) > 20  # JWT tokens are typically long
    
    # Decode token to verify content
    decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert decoded["sub"] == email
    assert "exp" in decoded


async def test_get_email_from_token_success():
    """Test successful email extraction from token."""
    email = "test@example.com"
    token = create_access_token(email=email)
    
    extracted_email = get_email_from_token(token)
    assert extracted_email == email


async def test_get_email_from_token_invalid():
    """Test email extraction from invalid token."""
    invalid_token = "invalid.token.here"
    
    with pytest.raises(HTTPException) as exc_info:
        get_email_from_token(invalid_token)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "could not validate credentials" in str(exc_info.value.detail).lower()
