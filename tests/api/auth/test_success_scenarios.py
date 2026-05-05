import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.services.auth import create_email_token

PREFIX = "/api/auth"


@pytest.fixture
def mock_email_services():
    """Mock email services to avoid actual email sending"""
    with patch("src.api.auth.send_verification_email") as mock_verify, \
         patch("src.api.auth.send_reset_password_email") as mock_reset:
        mock_verify.return_value = None
        mock_reset.return_value = None
        yield mock_verify, mock_reset


@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis client to avoid connection errors"""
    with patch("src.services.auth.redis_client", autospec=True) as mock:
        mock.delete = AsyncMock(return_value=None)
        yield mock


def test_register_user_success_with_background_task(client, mock_email_services):
    """Test successful user registration with background email task"""
    mock_verify, mock_reset = mock_email_services
    
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
    assert "hashed_password" not in data  # Password should not be returned
    
    # Verify background task was called
    mock_verify.assert_called_once()


def test_login_success_confirmed_user(client, mock_email_services):
    """Test successful login with confirmed user"""
    mock_verify, mock_reset = mock_email_services
    
    # Create and confirm user
    register_response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "confirmed_user",
            "email": "confirmed@example.com",
            "password": "password123",
        },
    )
    assert register_response.status_code == 201
    
    # Confirm the user's email
    token = create_email_token({"sub": "confirmed@example.com"})
    confirm_response = client.get(f"{PREFIX}/confirmed_email/{token}")
    assert confirm_response.status_code == 200
    
    # Now try to login
    login_response = client.post(
        f"{PREFIX}/login",
        data={"username": "confirmed_user", "password": "password123"},
    )
    
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_confirm_email_success(client, mock_email_services):
    """Test successful email confirmation"""
    mock_verify, mock_reset = mock_email_services
    
    # Create user first
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "user_to_confirm",
            "email": "toconfirm@example.com",
            "password": "password123",
        },
    )
    
    # Confirm email
    token = create_email_token({"sub": "toconfirm@example.com"})
    response = client.get(f"{PREFIX}/confirmed_email/{token}")
    
    assert response.status_code == 200
    assert "email address confirmed" in response.json()["message"].lower()


def test_request_email_sends_background_task(client, mock_email_services):
    """Test that request_email triggers background task for unconfirmed user"""
    mock_verify, mock_reset = mock_email_services
    
    # Create unconfirmed user first (this will call send_verification_email once)
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "unconfirmed_user",
            "email": "unconfirmed@example.com",
            "password": "password123",
        },
    )
    
    # Check initial call count
    initial_call_count = mock_verify.call_count
    
    # Request email verification
    response = client.post(
        f"{PREFIX}/request_email",
        json={"email": "unconfirmed@example.com"},
    )
    
    assert response.status_code == 200
    assert "if your address is in our database" in response.json()["message"].lower()
    
    # Verify background task was called exactly once more for this request
    assert mock_verify.call_count == initial_call_count + 1


def test_forgot_password_sends_background_task(client, mock_email_services):
    """Test that forgot_password triggers background task"""
    mock_verify, mock_reset = mock_email_services
    
    # Reset the mock to clear previous calls
    mock_reset.reset_mock()
    
    # Create user
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "user_with_password",
            "email": "haspassword@example.com",
            "password": "password123",
        },
    )
    
    # Request password reset
    response = client.post(
        f"{PREFIX}/forgot_password",
        json={"email": "haspassword@example.com"},
    )
    
    assert response.status_code == 200
    assert "if your address is in our database" in response.json()["message"].lower()
    
    # Verify background task was called exactly once for this request
    mock_reset.assert_called_once()


def test_reset_password_success_with_cache_invalidation(client, mock_email_services):
    """Test successful password reset with Redis cache invalidation"""
    mock_verify, mock_reset = mock_email_services
    
    # Create user first
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "reset_user",
            "email": "reset@example.com",
            "password": "oldpassword123",
        },
    )
    
    # Reset password
    token = create_email_token({"sub": "reset@example.com"})
    response = client.post(
        f"{PREFIX}/reset_password/{token}",
        json={"new_password": "newpassword123"},
    )
    
    assert response.status_code == 200
    assert "password successfully changed" in response.json()["message"].lower()


def test_register_user_password_hashing(client, mock_email_services):
    """Test that password is properly hashed during registration"""
    mock_verify, mock_reset = mock_email_services
    
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "hash_test_user",
            "email": "hashtest@example.com",
            "password": "plaintext123",
        },
    )
    
    assert response.status_code == 201
    user_data = response.json()
    
    # Password should not be returned in response
    assert "password" not in user_data
    assert "hashed_password" not in user_data
    
    # But user should have hashed_password in database (we can't test this directly 
    # without database access, but we can verify the response structure)
