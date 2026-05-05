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


def test_register_user_successful_flow(client):
    """Test successful registration flow to cover lines 48-67"""
    # Test with unique email and username to avoid conflicts
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "unique_user_123",
            "email": "unique123@example.com",
            "password": "password123",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "unique_user_123"
    assert data["email"] == "unique123@example.com"


def test_login_successful_flow(client):
    """Test successful login flow to cover lines 90-103"""
    # First create and confirm a user
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "login_success_user",
            "email": "loginsuccess@example.com",
            "password": "password123",
        },
    )
    
    # Confirm the user's email
    token = create_email_token({"sub": "loginsuccess@example.com"})
    client.get(f"{PREFIX}/confirmed_email/{token}")
    
    # Now login successfully
    response = client.post(
        f"{PREFIX}/login",
        data={"username": "login_success_user", "password": "password123"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_confirm_email_successful_flow(client):
    """Test successful email confirmation to cover lines 123-130"""
    # Create user first
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "confirm_success_user",
            "email": "confirmsuccess@example.com",
            "password": "password123",
        },
    )
    
    # Confirm email (this covers the success path)
    token = create_email_token({"sub": "confirmsuccess@example.com"})
    response = client.get(f"{PREFIX}/confirmed_email/{token}")
    
    assert response.status_code == 200
    assert "email address confirmed" in response.json()["message"].lower()


def test_confirm_email_already_confirmed_flow(client):
    """Test already confirmed email to cover line 128"""
    # Create and confirm user
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "already_confirmed_user",
            "email": "alreadyconfirmed@example.com",
            "password": "password123",
        },
    )
    
    token = create_email_token({"sub": "alreadyconfirmed@example.com"})
    client.get(f"{PREFIX}/confirmed_email/{token}")
    
    # Try to confirm again (covers line 128)
    response = client.get(f"{PREFIX}/confirmed_email/{token}")
    
    assert response.status_code == 200
    assert "already confirmed" in response.json()["message"].lower()


def test_request_email_for_unconfirmed_user(client):
    """Test request email for unconfirmed user to cover lines 158-172"""
    # Create unconfirmed user
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "request_email_user",
            "email": "requestemail@example.com",
            "password": "password123",
        },
    )
    
    # Request email (covers the success path for unconfirmed user)
    response = client.post(
        f"{PREFIX}/request_email",
        json={"email": "requestemail@example.com"},
    )
    
    assert response.status_code == 200
    assert "if your address is in our database" in response.json()["message"].lower()


def test_forgot_password_for_existing_user(client):
    """Test forgot password for existing user to cover lines 199-205"""
    # Create user
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "forgot_password_user",
            "email": "forgotpassword@example.com",
            "password": "password123",
        },
    )
    
    # Request password reset (covers the success path)
    response = client.post(
        f"{PREFIX}/forgot_password",
        json={"email": "forgotpassword@example.com"},
    )
    
    assert response.status_code == 200
    assert "if your address is in our database" in response.json()["message"].lower()


def test_reset_password_successful_flow(client):
    """Test successful password reset to cover lines 233-248"""
    # Create user first
    client.post(
        f"{PREFIX}/register",
        json={
            "username": "reset_password_user",
            "email": "resetpassword@example.com",
            "password": "oldpassword123",
        },
    )
    
    # Reset password (covers the success path)
    token = create_email_token({"sub": "resetpassword@example.com"})
    response = client.post(
        f"{PREFIX}/reset_password/{token}",
        json={"new_password": "newpassword123"},
    )
    
    assert response.status_code == 200
    assert "password successfully changed" in response.json()["message"].lower()


def test_register_user_no_conflicts(client):
    """Test registration with no email/username conflicts to cover success path"""
    # This test ensures we go through the success path (lines 61-67)
    response = client.post(
        f"{PREFIX}/register",
        json={
            "username": "no_conflict_user",
            "email": "noconflict@example.com",
            "password": "password123",
        },
    )
    
    # Should succeed (no conflicts)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "no_conflict_user"
    assert data["email"] == "noconflict@example.com"
