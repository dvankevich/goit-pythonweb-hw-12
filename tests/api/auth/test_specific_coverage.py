import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.services.auth import create_email_token

PREFIX = "/api/auth"


@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis client to avoid connection errors"""
    with patch("src.services.auth.redis_client", autospec=True) as mock:
        mock.delete = AsyncMock(return_value=None)
        yield mock


def test_register_user_no_email_conflict_to_cover_lines_48_52(client):
    """Test registration when no email conflict exists to cover lines 48-52"""
    # Use a unique email that definitely doesn't exist
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "no_email_conflict_user",
            "email": "noemailconflict12345@example.com",
            "password": "password123",
        },
    )
    
    # Should pass the email check (lines 48-52) and go to username check
    assert response.status_code in [201, 409]  # Either succeeds or username conflict


def test_register_user_no_username_conflict_to_cover_lines_54_58(client):
    """Test registration when no username conflict exists to cover lines 54-58"""
    # Use a unique username that definitely doesn't exist
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "no_username_conflict_12345",
            "email": "nounconflict@example.com",
            "password": "password123",
        },
    )
    
    # Should pass both checks and succeed
    assert response.status_code == 201


def test_login_user_exists_to_cover_lines_90_95(client):
    """Test login when user exists to cover lines 90-95"""
    # Create user first
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "login_exists_user",
            "email": "loginexists@example.com",
            "password": "password123",
        },
    )
    
    # Try to login (will fail at password check but covers user existence check)
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "login_exists_user", "password": "wrongpassword"},
    )
    
    # Should find user but fail password check
    assert response.status_code == 401


def test_login_password_correct_to_cover_lines_96_103(client):
    """Test login with correct password to cover lines 96-103"""
    # Create and confirm user
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "correct_password_user",
            "email": "correctpass@example.com",
            "password": "password123",
        },
    )
    
    # Confirm email
    token = create_email_token({"sub": "correctpass@example.com"})
    client.get(f"{PREFIX}/confirmed_email/{token}")
    
    # Login with correct password
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "correct_password_user", "password": "password123"},
    )
    
    # Should succeed
    assert response.status_code == 200


def test_confirm_email_user_exists_to_cover_lines_123_130(client):
    """Test email confirmation when user exists to cover lines 123-130"""
    # Create user first
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "confirm_exists_user",
            "email": "confirmexists@example.com",
            "password": "password123",
        },
    )
    
    # Confirm email (covers user existence check and success path)
    token = create_email_token({"sub": "confirmexists@example.com"})
    response = client.get(f"{PREFIX}/confirmed_email/{token}")
    
    assert response.status_code == 200


def test_request_email_user_exists_to_cover_lines_158_172(client):
    """Test request email when user exists to cover lines 158-172"""
    # Create unconfirmed user
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "request_exists_user",
            "email": "requestexists@example.com",
            "password": "password123",
        },
    )
    
    # Request email (covers user existence and background task)
    response = client.post(
        f"{PREFIX}/request_email",
        json={"email": "requestexists@example.com"},
    )
    
    assert response.status_code == 200


def test_request_email_user_not_confirmed_to_cover_background_task(client):
    """Test request email for unconfirmed user to ensure background task is called"""
    # Create unconfirmed user
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "unconfirmed_bg_user",
            "email": "unconfirmedbg@example.com",
            "password": "password123",
        },
    )
    
    # Mock the background task to verify it's called
    with patch("src.api.auth.send_verification_email") as mock_email:
        mock_email.return_value = None
        
        # Request email
        response = client.post(
            f"{PREFIX}/request_email",
            json={"email": "unconfirmedbg@example.com"},
        )
        
        assert response.status_code == 200
        # Verify background task was called
        mock_email.assert_called_once()


def test_forgot_password_user_exists_to_cover_lines_199_205(client):
    """Test forgot password when user exists to cover lines 199-205"""
    # Create user
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "forgot_exists_user",
            "email": "forgotexists@example.com",
            "password": "password123",
        },
    )
    
    # Request password reset (covers user existence and background task)
    response = client.post(
        f"{PREFIX}/forgot_password",
        json={"email": "forgotexists@example.com"},
    )
    
    assert response.status_code == 200


def test_reset_password_user_exists_to_cover_lines_233_248(client):
    """Test reset password when user exists to cover lines 233-248"""
    # Create user
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "reset_exists_user",
            "email": "resetexists@example.com",
            "password": "oldpassword123",
        },
    )
    
    # Reset password (covers user existence and success path)
    token = create_email_token({"sub": "resetexists@example.com"})
    response = client.post(
        f"{PREFIX}/reset_password/{token}",
        json={"new_password": "newpassword123"},
    )
    
    assert response.status_code == 200
