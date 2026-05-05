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
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "deadpool", "password": "123456"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    """Перевірка входу з неправильним паролем"""
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "deadpool", "password": "wrongpassword"},
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_user_not_found(client):
    """Перевірка входу неіснуючого користувача"""
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "nonexistent", "password": "password123"},
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_user_unconfirmed(client):
    """Перевірка входу непідтвердженого користувача"""
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "unconfirmed", "password": "123456"},
    )

    assert response.status_code == 401
    assert "email not confirmed" in response.json()["detail"].lower()


async def test_login_user_not_confirmed(client, db_session):
    """Перевірка входу непідтвердженого користувача (async version)"""
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "unconfirmed", "password": "123456"},
    )

    assert response.status_code == 401
    assert "email not confirmed" in response.json()["detail"].lower()
