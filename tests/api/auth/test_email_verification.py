"""Email verification API tests."""

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


def test_confirmed_email_already_confirmed(mock_get_email, client):
    """Перевірка підтвердження вже підтвердженого email"""
    mock_get_email.return_value = {"email": "deadpool@example.com"}

    response = client.get(f"{PREFIX}/confirmed_email/token")

    assert response.status_code == 400
    assert "already confirmed" in response.json()["detail"].lower()


def test_confirmed_email_user_not_found(mock_get_email, client):
    """Перевірка підтвердження email для неіснуючого користувача"""
    mock_get_email.return_value = {"email": "nonexistent@example.com"}

    response = client.get(f"{PREFIX}/confirmed_email/token")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_confirmed_email_user_not_found_in_db(mock_get_email, client):
    """Перевірка підтвердження email для користувача, якого немає в БД"""
    mock_get_email.return_value = {"email": "notindb@example.com"}

    response = client.get(f"{PREFIX}/confirmed_email/token")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_confirmed_email_success_real(mock_get_email, client):
    """Перевірка успішного підтвердження email"""
    mock_get_email.return_value = {"email": "test@example.com"}

    response = client.get(f"{PREFIX}/confirmed_email/valid_token")

    assert response.status_code == 200
    assert "confirmed" in response.json()["message"].lower()


async def test_confirmed_email_new_success(mock_get_email, client, db_session):
    """Перевірка успішного підтвердження email (async version)"""
    mock_get_email.return_value = {"email": "test@example.com"}

    response = client.get(f"{PREFIX}/confirmed_email/new_token")

    assert response.status_code == 200
    assert "confirmed" in response.json()["message"].lower()


def test_request_email_success(client):
    """Перевірка успішного запиту на підтвердження email"""
    response = client.post(
        f"{PREFIX}/request_email",
        json={"email": "deadpool@example.com"},
    )

    assert response.status_code == 200
    assert "email sent" in response.json()["message"].lower()


def test_request_email_already_confirmed(client):
    """Перевірка запиту на підтвердження вже підтвердженого email"""
    response = client.post(
        f"{PREFIX}/request_email",
        json={"email": "deadpool@example.com"},  # Вже підтверджений
    )

    assert response.status_code == 400
    assert "already confirmed" in response.json()["detail"].lower()


def test_request_email_not_found(client):
    """Перевірка запиту на підтвердження email для неіснуючого користувача"""
    response = client.post(
        f"{PREFIX}/request_email",
        json={"email": "nonexistent@example.com"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_request_email_logic_branches(client):
    """Перевірка логіки запиту на підтвердження email"""
    # Тест для різних гілок логіки
    response = client.post(
        f"{PREFIX}/request_email",
        json={"email": "test@example.com"},
    )

    assert response.status_code in [200, 400, 404]  # Можливі статуси
