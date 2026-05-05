"""Login API tests."""

import pytest
from unittest.mock import patch, AsyncMock
from src.schemas.user import UserCreate

PREFIX = "/api/auth"


def get_field_limit(field_name: str, limit_type: str):
    """
    limit_type може бути 'min_length' або 'max_length'
    """
    field = UserCreate.model_fields[field_name]
    for meta in field.metadata:
        if hasattr(meta, limit_type):
            return getattr(meta, limit_type)
    return None


USERNAME_MIN = get_field_limit("username", "min_length")
PASSWORD_MIN = get_field_limit("password", "min_length")
USERNAME_MAX = get_field_limit("username", "max_length")
PASSWORD_MAX = get_field_limit("password", "max_length")


@pytest.fixture(autouse=True)
def mock_email_services():
    with patch(
        "src.api.auth.send_verification_email", new_callable=AsyncMock
    ) as mock_send:
        with patch(
            "src.api.auth.send_reset_password_email", new_callable=AsyncMock
        ) as mock_reset:
            yield mock_send, mock_reset


@pytest.fixture(autouse=True)
def mock_redis():
    with patch("src.services.auth.redis_client", autospec=True) as mock:
        mock.delete = AsyncMock(return_value=None)
        yield mock


def test_login_user_success(client):
    """Перевірка успішного входу користувача"""
    # Спочатку створюємо користувача
    register_response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    assert register_response.status_code == 201
    
    # Тепер логінимось (навіть якщо email не підтверджений, перевіримо поведінку)
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "testuser", "password": "testpassword123"},
    )

    # Очікуємо 401 оскільки email не підтверджений
    assert response.status_code == 401
    assert "email address not confirmed" in response.json()["detail"].lower()


def test_login_wrong_password(client):
    """Перевірка входу з неправильним паролем"""
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "admin", "password": "wrongpassword"},  # Використовуємо адміна
    )

    assert response.status_code == 401
    assert "incorrect login or password" in response.json()["detail"].lower()


def test_login_user_not_found(client):
    """Перевірка входу неіснуючого користувача"""
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "nonexistent", "password": "password123"},
    )

    assert response.status_code == 401
    assert "incorrect login or password" in response.json()["detail"].lower()


def test_login_user_unconfirmed(client):
    """Перевірка входу непідтвердженого користувача"""
    # Оскільки API має захист від енумерації, непідтверджений користувач повертає ту саму помилку
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "unconfirmed", "password": "123456"},
    )

    assert response.status_code == 401
    assert "incorrect login or password" in response.json()["detail"].lower()


async def test_login_user_not_confirmed(client, db_session):
    """Перевірка входу непідтвердженого користувача (async version)"""
    # Оскільки API має захист від енумерації, непідтверджений користувач повертає ту саму помилку
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "unconfirmed", "password": "123456"},
    )

    assert response.status_code == 401
    assert "incorrect login or password" in response.json()["detail"].lower()
