"""Password reset API tests."""

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


@pytest.fixture
def mock_get_email():
    """Mock for get_email_from_token function."""
    with patch("src.api.auth.get_email_from_token") as mock:
        yield mock


def test_forgot_password_success(client):
    """Перевірка успішного запиту на скидання пароля"""
    response = client.post(
        f"{PREFIX}/forgot_password",
        json={"email": "deadpool@example.com"},
    )

    assert response.status_code == 200
    assert "if your address is in our database, you will receive an email with password reset instructions." in response.json()["message"].lower()


def test_forgot_password_not_found(client):
    """Перевірка запиту на скидання пароля для неіснуючого користувача"""
    response = client.post(
        f"{PREFIX}/forgot_password",
        json={"email": "nonexistent@example.com"},
    )

    # API повертає 200 для захисту від енумерації
    assert response.status_code == 200
    assert "if your address is in our database, you will receive an email with password reset instructions." in response.json()["message"].lower()


def test_forgot_password_branches(client):
    """Перевірка логіки запиту на скидання пароля"""
    # Тест для різних гілок логіки
    response = client.post(
        f"{PREFIX}/forgot_password",
        json={"email": "test@example.com"},
    )

    assert response.status_code in [200, 404]  # Можливі статуси


def test_reset_password_success(mock_get_email, client, mock_redis):
    """Перевірка успішного скидання пароля"""
    mock_get_email.return_value = "deadpool@example.com"

    response = client.post(
        f"{PREFIX}/reset_password/token",
        json={"new_password": "newpassword123"},
    )

    assert response.status_code == 200
    assert "password successfully changed" in response.json()["message"].lower()


def test_reset_password_user_not_found(mock_get_email, client):
    """Перевірка скидання пароля для неіснуючого користувача"""
    mock_get_email.return_value = "nonexistent@example.com"

    response = client.post(
        f"{PREFIX}/reset_password/token",
        json={"new_password": "newpassword123"},
    )

    # API повертає 400 з помилкою верифікації для захисту від енумерації
    assert response.status_code == 400
    assert "invalid token or user not found" in response.json()["detail"].lower()


def test_reset_password_user_not_found_logic(mock_get_email, client):
    """Перевірка логіки скидання пароля для неіснуючого користувача"""
    mock_get_email.return_value = "notfound@example.com"

    response = client.post(
        f"{PREFIX}/reset_password/token",
        json={"new_password": "newpassword123"},
    )

    # API повертає 400 з помилкою верифікації для захисту від енумерації
    assert response.status_code == 400


def test_reset_password_full_flow(mock_get_email, client, mock_redis):
    """Перевірка повного потоку скидання пароля"""
    mock_get_email.return_value = "deadpool@example.com"

    # Крок 1: Запит на скидання
    response1 = client.post(
        f"{PREFIX}/forgot_password",
        json={"email": "deadpool@example.com"},
    )
    assert response1.status_code == 200

    # Крок 2: Скидання пароля
    response2 = client.post(
        f"{PREFIX}/reset_password/token",
        json={"new_password": "newpassword123"},
    )
    assert response2.status_code == 200
    assert "password successfully changed" in response2.json()["message"].lower()


async def test_reset_password_user_missing(mock_get_email, client):
    """Перевірка скидання пароля для відсутнього користувача (async version)"""
    mock_get_email.return_value = "missing@example.com"

    response = client.post(
        f"{PREFIX}/reset_password/token",
        json={"new_password": "newpassword123"},
    )

    # API повертає 400 з помилкою верифікації для захисту від енумерації
    assert response.status_code == 400
    assert "invalid token or user not found" in response.json()["detail"].lower()
