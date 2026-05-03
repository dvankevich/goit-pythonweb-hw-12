import pytest
from datetime import timedelta, datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from jose import jwt
from fastapi import HTTPException, status

from src.services.auth import (
    Hash,
    create_access_token,
    get_email_from_token,
    get_current_user,
    get_current_admin_user,
)
from src.models.user import User, UserRole
from src.config.app_config import settings

# ====================== TEST HASHING ======================


def test_password_hashing():
    hash_handler = Hash()
    password = "secret_password"
    hashed = hash_handler.get_password_hash(password)

    assert hashed != password
    assert hash_handler.verify_password(password, hashed) is True
    assert hash_handler.verify_password("wrong_password", hashed) is False


# ====================== TEST JWT TOKENS ======================


@pytest.mark.asyncio
async def test_create_access_token():
    data = {"sub": "test@example.com"}
    token = await create_access_token(data, expires_delta=60)

    payload = jwt.decode(
        token,
        settings.JWT_SECRET.get_secret_value(),
        algorithms=[settings.JWT_ALGORITHM],
    )
    assert payload["sub"] == "test@example.com"
    assert "exp" in payload


@pytest.mark.asyncio
async def test_get_email_from_token_success():
    email = "user@test.com"
    token = jwt.encode(
        {"sub": email, "exp": datetime.now(UTC) + timedelta(days=1)},
        settings.JWT_SECRET.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )

    result = await get_email_from_token(token)
    assert result == email


@pytest.mark.asyncio
async def test_get_email_from_token_invalid():
    with pytest.raises(HTTPException) as exc:
        await get_email_from_token("invalid_token_string")
    assert exc.value.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# ====================== TEST GET CURRENT USER ======================


@pytest.mark.asyncio
@patch("src.services.auth.redis_client")
@patch("src.services.auth.UserService")
async def test_get_current_user_cache_hit(mock_user_service, mock_redis, mock_session):
    # Налаштовуємо Redis Cache Hit
    mock_redis.get.return_value = (
        '{"id": 1, "username": "testuser", "email": "test@test.com", "role": "user"}'
    )

    token = jwt.encode(
        {"sub": "testuser"},
        settings.JWT_SECRET.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )

    user = await get_current_user(token=token, db=mock_session)

    assert user.username == "testuser"
    mock_redis.get.assert_called_once()
    # Якщо взяли з кешу, UserService не повинен викликатись
    mock_user_service.assert_not_called()


@pytest.mark.asyncio
@patch("src.services.auth.redis_client")
@patch("src.services.auth.UserService")
async def test_get_current_user_redis_error_fallback(
    mock_user_service_class, mock_redis, mock_session
):
    # Емулюємо помилку Redis
    mock_redis.get.side_effect = Exception("Redis is down")

    # Налаштовуємо повернення юзера з бази
    # Створюємо екземпляр сервісу як мок
    mock_user_service_instance = MagicMock()
    mock_user_service_class.return_value = mock_user_service_instance

    mock_user = User(
        id=1, username="testuser", email="test@test.com", role=UserRole.USER
    )

    #  AsyncMock для асинхронного методу
    mock_user_service_instance.get_user_by_username = AsyncMock(return_value=mock_user)

    token = jwt.encode(
        {"sub": "testuser"},
        settings.JWT_SECRET.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )

    user = await get_current_user(token=token, db=mock_session)

    assert user.username == "testuser"
    mock_user_service_instance.get_user_by_username.assert_called_once_with("testuser")


@pytest.mark.asyncio
@patch("src.services.auth.redis_client")
async def test_get_current_admin_user_success(mock_redis):
    admin_user = User(username="admin", role=UserRole.ADMIN)

    # Якщо адмін — повертаємо юзера
    result = await get_current_admin_user(current_user=admin_user)
    assert result == admin_user


@pytest.mark.asyncio
async def test_get_current_admin_user_forbidden():
    regular_user = User(username="user", role=UserRole.USER)

    # Якщо не адмін — очікуємо 403 помилку
    with pytest.raises(HTTPException) as exc:
        await get_current_admin_user(current_user=regular_user)
    assert exc.value.status_code == 403
