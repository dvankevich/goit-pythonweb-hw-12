"""Registration API tests."""

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


def test_register_user_success(client, mock_email_services):
    """Перевірка успішної реєстрації користувача"""
    mock_send, _ = mock_email_services  # Дістаємо мок відправки листа

    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "password" not in data
    mock_send.assert_called_once()


def test_register_user_already_exists(client):
    """Перевірка реєстрації існуючого користувача"""
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "deadpool",
            "email": "deadpool@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 409
    assert "user with this email already exists" in response.json()["detail"].lower()


def test_register_user_duplicate_username(client):
    """Перевірка реєстрації з дублікатним username"""
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "deadpool",  # Існуючий username
            "email": "newemail@example.com",  # Новий email
            "password": "password123",
        },
    )

    assert response.status_code == 409
    assert "user with this username already exists" in response.json()["detail"].lower()


def test_register_duplicate_username(client):
    """Перевірка реєстрації з дублікатним username (інший тест)"""
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "deadpool",
            "email": "different@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 409
    assert "user with this username already exists" in response.json()["detail"].lower()


def test_register_username_too_short(client):
    """Перевірка реєстрації з занадто коротким username"""
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "ab",  # Занадто короткий
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 422
    assert "username" in response.json()["detail"][0]["loc"]


def test_register_password_too_short(client):
    """Перевірка реєстрації з занадто коротким password"""
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "123",  # Занадто короткий
        },
    )

    assert response.status_code == 422
    assert "password" in response.json()["detail"][0]["loc"]


def test_register_username_too_long(client):
    """Перевірка реєстрації з занадто довгим username"""
    long_username = "a" * (USERNAME_MAX + 1)
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": long_username,
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 422
    assert "username" in response.json()["detail"][0]["loc"]


def test_register_password_too_long(client):
    """Перевірка реєстрації з занадто довгим password"""
    long_password = "a" * (PASSWORD_MAX + 1)
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": long_password,
        },
    )

    assert response.status_code == 422
    assert "password" in response.json()["detail"][0]["loc"]
