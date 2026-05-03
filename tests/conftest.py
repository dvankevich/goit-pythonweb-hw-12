import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User, UserRole


@pytest.fixture
def mock_session():
    """Універсальна сесія для репозиторіїв та сервісів"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user():
    """Базовий мок користувача для тестів авторизації та профілю"""
    return User(
        id=1,
        username="test_user",
        email="test@example.com",
        role=UserRole.USER,
        confirmed=True,
    )
