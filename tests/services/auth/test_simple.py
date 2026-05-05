"""Simple authentication service tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status

from src.services.auth import Hash, create_access_token, get_email_from_token
from src.config.app_config import settings


def test_hash_password():
    """Test password hashing."""
    hash_service = Hash()
    password = "test_password"
    
    # Test password hashing
    hashed = hash_service.get_password_hash(password)
    
    assert isinstance(hashed, str)
    assert hashed != password
    assert len(hashed) > 50  # bcrypt hashes are typically long


def test_verify_password():
    """Test password verification."""
    hash_service = Hash()
    password = "test_password"
    hashed = hash_service.get_password_hash(password)
    
    # Test correct password
    assert hash_service.verify_password(password, hashed) is True
    
    # Test incorrect password
    assert hash_service.verify_password("wrong_password", hashed) is False


def test_create_access_token():
    """Test JWT token creation."""
    email = "test@example.com"
    token = create_access_token(data={"sub": email})
    
    assert isinstance(token, str)
    assert len(token) > 20  # JWT tokens are typically long
    
    # Decode token to verify content
    from jose import jwt
    decoded = jwt.decode(token, settings.JWT_SECRET.get_secret_value(), algorithms=[settings.JWT_ALGORITHM])
    assert decoded["sub"] == email
    assert "exp" in decoded


def test_get_email_from_token_success():
    """Test successful email extraction from token."""
    email = "test@example.com"
    token = create_access_token(data={"sub": email})
    
    result = get_email_from_token(token)
    
    assert result == email


def test_get_email_from_token_invalid():
    """Test email extraction from invalid token."""
    invalid_token = "invalid.token.here"
    
    with pytest.raises(HTTPException) as exc_info:
        get_email_from_token(invalid_token)
    
    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "invalid token" in str(exc_info.value.detail).lower()
