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


# --- ТЕСТИ РЕЄСТРАЦІЇ ---


def test_register_user_success(client, mock_email_services):
    mock_send, _ = mock_email_services  # Дістаємо мок відправки листа

    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "new_hero",
            "email": "new_hero@example.com",
            "password": "strongpassword123",
        },
    )
    assert response.status_code == 201
    # Перевіряємо, що фонова задача була додана (лист "відправлено")
    assert mock_send.called
    # Перевіряємо, чи правильному адресату
    assert mock_send.call_args[0][0] == "new_hero@example.com"


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


# --- ДОДАТКОВІ ТЕСТИ РЕЄСТРАЦІЇ ---


def test_register_user_duplicate_username(client):
    """Перевірка помилки при існуючому username, але іншому email"""
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "deadpool",  # Вже існує
            "email": "another_email@example.com",
            "password": "somepassword",
        },
    )
    assert response.status_code == 409
    assert "з таким іменем вже існує" in response.json()["detail"]


# --- ДОДАТКОВІ ТЕСТИ ЛОГІНУ ---


def test_login_user_not_found(client):
    """Спроба логіну під неіснуючим користувачем"""
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "ghost_user", "password": "password"},
    )
    assert response.status_code == 401
    assert "Неправильний логін або пароль" in response.json()["detail"]


def test_login_user_unconfirmed(client):
    """Спроба логіну з непідтвердженою поштою"""
    # 1. Реєструємо нового юзера (за замовчуванням confirmed=False)
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "unconfirmed_user",
            "email": "unconfirmed@example.com",
            "password": "password123",
        },
    )
    # 2. Пробуємо залогінитись
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "unconfirmed_user", "password": "password123"},
    )
    assert response.status_code == 401
    assert "не підтверджена" in response.json()["detail"]


# --- ДОДАТКОВІ ТЕСТИ ПІДТВЕРДЖЕННЯ EMAIL ---


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_confirmed_email_user_not_found(mock_get_email, client):
    """Коли токен валідний, але користувача з таким email немає в базі"""
    mock_get_email.return_value = "ghost@example.com"
    response = client.get(f"{PREFIX}/confirmed_email/valid_token")
    assert response.status_code == 400
    assert "Verification error" in response.json()["detail"]


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_confirmed_email_user_not_found_in_db(mock_get_email, client):
    # Токен валідний, повертає імейл, але в базі такого юзера немає
    mock_get_email.return_value = "unknown@example.com"
    response = client.get(f"{PREFIX}/confirmed_email/valid_token")
    assert response.status_code == 400
    assert response.json()["detail"] == "Verification error"


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_confirmed_email_success_real(mock_get_email, client):
    """Успішне підтвердження пошти для непідтвердженого юзера"""
    # Використовуємо юзера з попереднього тесту
    mock_get_email.return_value = "unconfirmed@example.com"
    response = client.get(f"{PREFIX}/confirmed_email/valid_token")
    assert response.status_code == 200
    assert "підтверджено" in response.json()["message"]


# --- ТЕСТИ REQUEST EMAIL ---


def test_request_email_success(client):
    """Запит на лист для існуючого і непідтвердженого користувача"""
    response = client.post(
        f"{PREFIX}/request_email", json={"email": "unconfirmed@example.com"}
    )
    assert response.status_code == 200
    assert "ви отримаєте лист" in response.json()["message"]


def test_request_email_already_confirmed(client):
    """Запит на лист для вже підтвердженого користувача (deadpool)"""
    response = client.post(
        f"{PREFIX}/request_email", json={"email": "deadpool@example.com"}
    )
    assert response.status_code == 200


def test_request_email_not_found(client):
    """Запит на лист для неіснуючого користувача"""
    response = client.post(
        f"{PREFIX}/request_email", json={"email": "ghost@example.com"}
    )
    # Відповідь завжди 200, щоб уникнути енумерації
    assert response.status_code == 200


# --- ДОДАТКОВІ ТЕСТИ СКИДАННЯ ПАРОЛЯ ---


def test_forgot_password_not_found(client):
    """Запит на скидання пароля для неіснуючого юзера"""
    response = client.post(
        f"{PREFIX}/forgot_password", json={"email": "ghost@example.com"}
    )
    # Відповідь має бути 200 незалежно від наявності юзера
    assert response.status_code == 200


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_reset_password_user_not_found(mock_get_email, client):
    """Спроба скинути пароль з токеном неіснуючого юзера"""
    mock_get_email.return_value = "ghost@example.com"
    response = client.post(
        f"{PREFIX}/reset_password/some_token", json={"new_password": "newpassword123"}
    )
    assert response.status_code == 400
    assert "Недійсний токен" in response.json()["detail"]


# ------


@pytest.mark.asyncio
@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
async def test_confirmed_email_new_success(mock_get_email, client, db_session):
    """Тест переходу непідтвердженого користувача в підтверджений"""
    from src.models.user import User

    email = "fresh_user@example.com"
    new_user = User(
        username="fresh_user",
        email=email,
        hashed_password="hashed_password_123",
        confirmed=False,
    )

    db_session.add(new_user)
    await db_session.commit()
    await db_session.refresh(new_user)  # Оновлюємо об'єкт з бази

    mock_get_email.return_value = email

    response = client.get(f"{PREFIX}/confirmed_email/some_token")

    assert response.status_code == 200
    assert "підтверджено" in response.json()["message"]


def test_request_email_logic_branches(client):
    """Покриття рядків 107-121 (request_email)"""
    # Гілка: юзера не існує
    resp = client.post(
        f"{PREFIX}/request_email", json={"email": "nonexistent@example.com"}
    )
    assert resp.status_code == 200

    # Гілка: юзер вже підтверджений
    resp = client.post(
        f"{PREFIX}/request_email", json={"email": "deadpool@example.com"}
    )
    assert resp.status_code == 200


def test_forgot_password_branches(client):
    """Покриття рядків 135-141 (forgot_password)"""
    # Юзер існує (deadpool) - має спрацювати background task
    resp = client.post(
        f"{PREFIX}/forgot_password", json={"email": "deadpool@example.com"}
    )
    assert resp.status_code == 200

    # Юзер не існує
    resp = client.post(f"{PREFIX}/forgot_password", json={"email": "ghost@example.com"})
    assert resp.status_code == 200


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_reset_password_user_not_found_logic(mock_get_email, client):
    """Покриття рядків 156-171 (якщо юзера не знайдено за імейлом з токена)"""
    mock_get_email.return_value = "never_existed@example.com"
    response = client.post(
        f"{PREFIX}/reset_password/token", json={"new_password": "new_pass_123"}
    )
    assert response.status_code == 400
    assert "користувача не знайдено" in response.json()["detail"]


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_reset_password_full_flow(mock_get_email, client, mock_redis):
    # Підготовка: імейл deadpool
    email = "deadpool@example.com"
    mock_get_email.return_value = email

    response = client.post(
        f"{PREFIX}/reset_password/some_token",
        json={"new_password": "brand_new_password_123"},
    )

    assert response.status_code == 200
    # Перевіряємо, чи видалено ключ з Redis (рядок 168-169 у твоєму api/auth.py)
    mock_redis.delete.assert_called_with(f"user:deadpool")


def test_register_duplicate_username(client):
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "deadpool",  # вже є в базі
            "email": "unique_hero@example.com",
            "password": "password",
        },
    )
    assert response.status_code == 409
    assert "іменем вже існує" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_user_not_confirmed(client, db_session):
    from src.models.user import User
    from src.services.auth import Hash

    raw_password = "testpassword123"
    hashed = Hash().get_password_hash(raw_password)

    user = User(
        username="lazy_user",
        email="lazy@ex.com",
        hashed_password=hashed,
        confirmed=False,
    )
    db_session.add(user)
    await db_session.commit()

    response = client.post(
        f"{PREFIX}/login", data={"username": "lazy_user", "password": raw_password}
    )
    assert response.status_code == 401
    assert "не підтверджена" in response.json()["detail"]


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
async def test_reset_password_user_missing(mock_get_email, client):
    mock_get_email.return_value = (
        "deleted_user@example.com"  # Такого email немає в базі
    )
    response = client.post(
        f"{PREFIX}/reset_password/token", json={"new_password": "testpassword123"}
    )
    assert response.status_code == 400
    assert "користувача не знайдено" in response.json()["detail"]


def test_register_username_too_short(client):
    invalid_username = "a" * (USERNAME_MIN - 1)  # type: ignore

    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": invalid_username,
            "email": "valid@example.com",
            "password": "strongpassword123",
        },
    )
    assert response.status_code == 422
    # Перевіряємо, чи вказана правильна кількість у повідомленні помилки
    error_msg = response.json()["detail"][0]["msg"]
    assert f"at least {USERNAME_MIN} characters" in error_msg


def test_register_password_too_short(client):
    invalid_password = "p" * (PASSWORD_MIN - 1)  # type: ignore

    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "valid_user",
            "email": "valid@example.com",
            "password": invalid_password,
        },
    )
    assert response.status_code == 422
    error_msg = response.json()["detail"][0]["msg"]
    assert f"at least {PASSWORD_MIN} characters" in error_msg


def test_register_username_too_long(client):
    invalid_username = "a" * (USERNAME_MAX + 1)  # type: ignore

    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": invalid_username,
            "email": "valid@example.com",
            "password": "strongpassword123",
        },
    )
    assert response.status_code == 422
    error_msg = response.json()["detail"][0]["msg"]
    assert f"at most {USERNAME_MAX} characters" in error_msg


def test_register_password_too_long(client):
    invalid_password = "p" * (PASSWORD_MAX + 1)  # type: ignore

    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "valid_user",
            "email": "valid@example.com",
            "password": invalid_password,
        },
    )
    assert response.status_code == 422
    error_msg = response.json()["detail"][0]["msg"]
    assert f"at most {PASSWORD_MAX} characters" in error_msg
