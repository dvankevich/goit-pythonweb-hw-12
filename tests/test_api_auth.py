import pytest
from unittest.mock import patch, AsyncMock

# Визначаємо префікс, як у вашому робочому прикладі
PREFIX = "/api/auth"


@pytest.fixture(autouse=True)
def mock_email_services():
    # Важливо: шлях до мока має відповідати тому, де імпортована функція.
    # Якщо роутер в src/api/auth.py, то шлях src.api.auth.send_email
    with patch("src.api.auth.send_email", new_callable=AsyncMock) as mock_send:
        with patch(
            "src.api.auth.send_reset_password_email", new_callable=AsyncMock
        ) as mock_reset:
            yield mock_send, mock_reset


@pytest.fixture(autouse=True)
def mock_redis():
    with patch("src.services.auth.redis_client", autospec=True) as mock:
        mock.delete = AsyncMock(return_value=None)
        yield mock


# --- ТЕСТИ РЕЄСТРАЦІЇ ---


def test_register_user_success(client):
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "new_hero",
            "email": "new_hero@example.com",
            "password": "strongpassword123",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == "new_hero"
    assert data["email"] == "new_hero@example.com"


def test_register_user_already_exists(client):
    # deadpool вже створений у conftest.py
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "deadpool",
            "email": "deadpool@example.com",
            "password": "somepassword",
        },
    )
    assert response.status_code == 409
    assert "вже існує" in response.json()["detail"]


# --- ТЕСТИ ЛОГІНУ ---


def test_login_user_success(client):
    # Дані deadpool з conftest.py
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "deadpool", "password": "secretpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data


def test_login_wrong_password(client):
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "deadpool", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Неправильний логін" in response.json()["detail"]


# --- ТЕСТИ ПІДТВЕРДЖЕННЯ EMAIL ---


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_confirmed_email_already_confirmed(mock_get_email, client):
    mock_get_email.return_value = "deadpool@example.com"

    # deadpool у conftest має confirmed=True
    response = client.get(f"{PREFIX}/confirmed_email/valid_token")
    assert response.status_code == 200
    assert "вже підтверджена" in response.json()["message"]


# --- ТЕСТИ ПАРОЛЯ ---


def test_forgot_password_success(client):
    response = client.post(
        f"{PREFIX}/forgot_password", json={"email": "deadpool@example.com"}
    )
    assert response.status_code == 200
    assert "інструкціями" in response.json()["message"]


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_reset_password_success(mock_get_email, client, mock_redis):
    mock_get_email.return_value = "deadpool@example.com"

    response = client.post(
        f"{PREFIX}/reset_password/some_token", json={"new_password": "newpassword123"}
    )
    assert response.status_code == 200
    assert "Пароль успішно змінено" in response.json()["message"]
