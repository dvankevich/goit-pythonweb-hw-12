"""User authentication service tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status

from src.services.auth import get_current_user, get_current_admin_user
from src.models import User, UserRole


@pytest.fixture
def mock_user():
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        confirmed=True,
        role=UserRole.USER,
    )


@pytest.fixture
def mock_admin_user():
    return User(
        id=2,
        username="admin",
        email="admin@example.com",
        hashed_password="hashed_password",
        confirmed=True,
        role=UserRole.ADMIN,
    )


@pytest.fixture
def mock_user_service():
    return AsyncMock()


@pytest.fixture
def mock_redis():
    return AsyncMock()


@pytest.fixture
def mock_session():
    return AsyncMock()


async def test_get_current_user_cache_hit(mock_user_service, mock_redis, mock_session):
    """Test getting current user from cache (cache hit)."""
    mock_user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        confirmed=True,
        role=UserRole.USER,
    )
    
    # Mock Redis cache hit
    mock_redis.get.return_value = '{"id": 1, "username": "testuser", "email": "test@example.com"}'
    
    with patch('src.services.users.UserRepository') as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_user_by_email.return_value = mock_user
        
        # Mock the token dependency
        mock_token = "fake_token"
        
        result = await get_current_user(mock_token, mock_session, mock_redis)
        
        assert result.email == "test@example.com"
        assert result.username == "testuser"
        mock_redis.get.assert_called_once()


async def test_get_current_user_redis_error_fallback(mock_session):
    """Test getting current user with Redis error (fallback to DB)."""
    mock_user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        confirmed=True,
        role=UserRole.USER,
    )
    
    # Mock Redis error
    mock_redis = AsyncMock()
    mock_redis.get.side_effect = Exception("Redis connection error")
    
    with patch('src.services.users.UserRepository') as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_user_by_email.return_value = mock_user
        
        # Mock the token dependency
        mock_token = "fake_token"
        
        result = await get_current_user(mock_token, mock_session, mock_redis)
        
        assert result.email == "test@example.com"
        assert result.username == "testuser"
        mock_repo.get_user_by_email.assert_called_once_with("test@example.com")


async def test_get_current_admin_user_success():
    """Test getting current admin user successfully."""
    mock_admin = User(
        id=2,
        username="admin",
        email="admin@example.com",
        hashed_password="hashed_password",
        confirmed=True,
        role=UserRole.ADMIN,
    )
    
    # Test get_current_admin_user function directly with admin user
    result = await get_current_admin_user(mock_admin)
    
    assert result.role == UserRole.ADMIN
    assert result.email == "admin@example.com"


async def test_get_current_admin_user_forbidden():
    """Test getting current admin user with regular user (should fail)."""
    mock_regular_user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        confirmed=True,
        role=UserRole.USER,  # Regular user, not admin
    )
    
    with patch('src.services.auth.get_current_user') as mock_get_current:
        mock_get_current.return_value = mock_regular_user
    
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(mock_regular_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "enough privileges" in str(exc_info.value.detail).lower()
