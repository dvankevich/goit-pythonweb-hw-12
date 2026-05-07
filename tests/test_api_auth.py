import pytest
from unittest.mock import patch, AsyncMock
from src.schemas.user import UserCreate

PREFIX = "/api/auth"


def get_field_limit(field_name: str, limit_type: str):
    """
    limit_type can be 'min_length' or 'max_length'
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


# --- REGISTRATION TESTS ---


def test_register_user_success(client, mock_email_services):
    mock_send, _ = mock_email_services  # Get the email sending mock

    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "new_hero",
            "email": "new_hero@example.com",
            "password": "strongpassword123",
        },
    )
    assert response.status_code == 201
    # Check that background task was added (email "sent")
    assert mock_send.called
    # Check that it's for the correct recipient
    assert mock_send.call_args[0][0] == "new_hero@example.com"


def test_register_user_already_exists(client):
    # deadpool is already created in conftest.py
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "deadpool",
            "email": "deadpool@example.com",
            "password": "somepassword",
        },
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


# --- LOGIN TESTS ---


def test_login_user_success(client):
    # deadpool data from conftest.py
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
    assert "Invalid login or password" in response.json()["detail"]


# --- EMAIL CONFIRMATION TESTS ---


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_confirmed_email_already_confirmed(mock_get_email, client):
    mock_get_email.return_value = "deadpool@example.com"

    # deadpool in conftest has confirmed=True
    response = client.get(f"{PREFIX}/confirmed_email/valid_token")
    assert response.status_code == 200
    assert "already confirmed" in response.json()["message"]


# --- PASSWORD TESTS ---


def test_forgot_password_success(client):
    response = client.post(
        f"{PREFIX}/forgot_password", json={"email": "deadpool@example.com"}
    )
    assert response.status_code == 200
    assert "instructions" in response.json()["message"]


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_reset_password_success(mock_get_email, client, mock_redis):
    mock_get_email.return_value = "deadpool@example.com"

    response = client.post(
        f"{PREFIX}/reset_password/some_token", json={"new_password": "newpassword123"}
    )
    assert response.status_code == 200
    assert "Password successfully changed" in response.json()["message"]


# --- ADDITIONAL REGISTRATION TESTS ---


def test_register_user_duplicate_username(client):
    """Check error for existing username with different email"""
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "deadpool",  # Already exists
            "email": "another_email@example.com",
            "password": "somepassword",
        },
    )
    assert response.status_code == 409
    assert "with this name already exists" in response.json()["detail"]


# --- ADDITIONAL LOGIN TESTS ---


def test_login_user_not_found(client):
    """Attempt login with non-existent user"""
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "ghost_user", "password": "password"},
    )
    assert response.status_code == 401
    assert "Invalid login or password" in response.json()["detail"]


def test_login_user_unconfirmed(client):
    """Attempt login with unconfirmed email"""
    # 1. Register new user (default confirmed=False)
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "unconfirmed_user",
            "email": "unconfirmed@example.com",
            "password": "password123",
        },
    )
    # 2. Try to login
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "unconfirmed_user", "password": "password123"},
    )
    assert response.status_code == 401
    assert "not confirmed" in response.json()["detail"]


# --- ADDITIONAL EMAIL CONFIRMATION TESTS ---


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_confirmed_email_user_not_found(mock_get_email, client):
    """When token is valid but user with such email doesn't exist in database"""
    mock_get_email.return_value = "ghost@example.com"
    response = client.get(f"{PREFIX}/confirmed_email/valid_token")
    assert response.status_code == 400
    assert "Verification error" in response.json()["detail"]


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_confirmed_email_user_not_found_in_db(mock_get_email, client):
    # Token is valid, returns email, but no such user in database
    mock_get_email.return_value = "unknown@example.com"
    response = client.get(f"{PREFIX}/confirmed_email/valid_token")
    assert response.status_code == 400
    assert response.json()["detail"] == "Verification error"


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_confirmed_email_success_real(mock_get_email, client):
    """Successful email confirmation for unconfirmed user"""
    # Use user from previous test
    mock_get_email.return_value = "unconfirmed@example.com"
    response = client.get(f"{PREFIX}/confirmed_email/valid_token")
    assert response.status_code == 200
    assert "confirmed" in response.json()["message"]


# --- REQUEST EMAIL TESTS ---


def test_request_email_success(client):
    """Request email for existing and unconfirmed user"""
    response = client.post(
        f"{PREFIX}/request_email", json={"email": "unconfirmed@example.com"}
    )
    assert response.status_code == 200
    assert "in our database" in response.json()["message"]


def test_request_email_already_confirmed(client):
    """Request email for already confirmed user (deadpool)"""
    response = client.post(
        f"{PREFIX}/request_email", json={"email": "deadpool@example.com"}
    )
    assert response.status_code == 200


def test_request_email_not_found(client):
    """Request email for non-existent user"""
    response = client.post(
        f"{PREFIX}/request_email", json={"email": "ghost@example.com"}
    )
    # Response is always 200 to avoid enumeration
    assert response.status_code == 200


# --- ADDITIONAL PASSWORD RESET TESTS ---


def test_forgot_password_not_found(client):
    """Request password reset for non-existent user"""
    response = client.post(
        f"{PREFIX}/forgot_password", json={"email": "ghost@example.com"}
    )
    # Response should be 200 regardless of user existence
    assert response.status_code == 200


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_reset_password_user_not_found(mock_get_email, client):
    """Attempt password reset with token of non-existent user"""
    mock_get_email.return_value = "ghost@example.com"
    response = client.post(
        f"{PREFIX}/reset_password/some_token", json={"new_password": "newpassword123"}
    )
    assert response.status_code == 400
    assert "Invalid token" in response.json()["detail"]


# ------


@pytest.mark.asyncio
@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
async def test_confirmed_email_new_success(mock_get_email, client, db_session):
    """Test transition of unconfirmed user to confirmed"""
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
    await db_session.refresh(new_user)  # Update object from database

    mock_get_email.return_value = email

    response = client.get(f"{PREFIX}/confirmed_email/some_token")

    assert response.status_code == 200
    assert "confirmed" in response.json()["message"]


def test_request_email_logic_branches(client):
    """Coverage of lines 107-121 (request_email)"""
    # Branch: user doesn't exist
    resp = client.post(
        f"{PREFIX}/request_email", json={"email": "nonexistent@example.com"}
    )
    assert resp.status_code == 200

    # Branch: user already confirmed
    resp = client.post(
        f"{PREFIX}/request_email", json={"email": "deadpool@example.com"}
    )
    assert resp.status_code == 200


def test_forgot_password_branches(client):
    """Coverage of lines 135-141 (forgot_password)"""
    # User exists (deadpool) - should trigger background task
    resp = client.post(
        f"{PREFIX}/forgot_password", json={"email": "deadpool@example.com"}
    )
    assert resp.status_code == 200

    # User doesn't exist
    resp = client.post(f"{PREFIX}/forgot_password", json={"email": "ghost@example.com"})
    assert resp.status_code == 200


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_reset_password_user_not_found_logic(mock_get_email, client):
    """Coverage of lines 156-171 (if user not found by email from token)"""
    mock_get_email.return_value = "never_existed@example.com"
    response = client.post(
        f"{PREFIX}/reset_password/token", json={"new_password": "new_pass_123"}
    )
    assert response.status_code == 400
    assert "user not found" in response.json()["detail"]


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
def test_reset_password_full_flow(mock_get_email, client, mock_redis):
    # Preparation: deadpool email
    email = "deadpool@example.com"
    mock_get_email.return_value = email

    response = client.post(
        f"{PREFIX}/reset_password/some_token",
        json={"new_password": "brand_new_password_123"},
    )

    assert response.status_code == 200
    # Check if Redis key was deleted (line 168-169 in your api/auth.py)
    mock_redis.delete.assert_called_with(f"user:deadpool")


def test_register_duplicate_username(client):
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "deadpool",  # already in database
            "email": "unique_hero@example.com",
            "password": "password",
        },
    )
    assert response.status_code == 409
    assert "with this name already exists" in response.json()["detail"]


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
    assert "not confirmed" in response.json()["detail"]


@patch("src.api.auth.get_email_from_token", new_callable=AsyncMock)
async def test_reset_password_user_missing(mock_get_email, client):
    mock_get_email.return_value = (
        "deleted_user@example.com"  # No such email in database
    )
    response = client.post(
        f"{PREFIX}/reset_password/token", json={"new_password": "testpassword123"}
    )
    assert response.status_code == 400
    assert "user not found" in response.json()["detail"]


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
    # Check if correct quantity is specified in error message
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
