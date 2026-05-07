import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status

# API prefix from your router
PREFIX = "/api/auth"

# --- REGISTRATION BRANCHES (Lines 48-67) ---


@pytest.mark.asyncio
async def test_register_user_email_exists(client):
    """Coverage for email conflict branch (Lines 48-53)"""
    with patch(
        "src.api.auth.UserService.get_user_by_email", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = MagicMock(id=1)  # User exists

        response = client.post(
            f"{PREFIX}/register",
            json={
                "username": "new",
                "email": "exists@ex.com",
                "password": "password123",
            },
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "email already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_user_username_exists(client):
    """Coverage for username conflict branch (Lines 55-60)"""
    with patch(
        "src.api.auth.UserService.get_user_by_email", new_callable=AsyncMock
    ) as mock_email:
        with patch(
            "src.api.auth.UserService.get_user_by_username", new_callable=AsyncMock
        ) as mock_user:
            mock_email.return_value = None
            mock_user.return_value = MagicMock(id=1)  # Username taken

            response = client.post(
                f"{PREFIX}/register",
                json={
                    "username": "taken",
                    "email": "new@ex.com",
                    "password": "password123",
                },
            )
            assert response.status_code == status.HTTP_409_CONFLICT
            assert "name already exists" in response.json()["detail"]


# --- LOGIN BRANCHES (Lines 90-103) ---


@pytest.mark.asyncio
async def test_login_user_not_confirmed(client):
    """Coverage for unconfirmed email branch (Lines 101-103)"""
    with patch(
        "src.api.auth.UserService.get_user_by_username", new_callable=AsyncMock
    ) as mock_get:
        # Mock user exists, password is correct, but NOT confirmed
        mock_user = MagicMock()
        mock_user.hashed_password = "hashed_password"
        mock_user.confirmed = False
        mock_get.return_value = mock_user

        with patch("src.api.auth.Hash.verify_password", return_value=True):
            response = client.post(
                f"{PREFIX}/login", data={"username": "test", "password": "password"}
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "not confirmed" in response.json()["detail"]


# --- CONFIRMATION BRANCHES (Lines 123-130) ---


@pytest.mark.asyncio
async def test_confirmed_email_user_none(client):
    """Coverage for verification error when user is not found (Lines 123-130)"""
    with patch(
        "src.api.auth.get_email_from_token", new_callable=AsyncMock
    ) as mock_token:
        with patch(
            "src.api.auth.UserService.get_user_by_email", new_callable=AsyncMock
        ) as mock_user:
            mock_token.return_value = "some@ex.com"
            mock_user.return_value = None  # User not found

            response = client.get(f"{PREFIX}/confirmed_email/some_token")
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Verification error" in response.json()["detail"]


# --- REQUEST EMAIL BRANCHES (Lines 158-172) ---


@pytest.mark.asyncio
async def test_request_email_branches(client):
    """Coverage for generic messages in request_email (Lines 158-172)"""
    with patch(
        "src.api.auth.UserService.get_user_by_email", new_callable=AsyncMock
    ) as mock_get:
        # Case 1: User is None
        mock_get.return_value = None
        resp1 = client.post(f"{PREFIX}/request_email", json={"email": "none@ex.com"})
        assert resp1.status_code == 200

        # Case 2: User already confirmed
        mock_user = MagicMock(confirmed=True)
        mock_get.return_value = mock_user
        resp2 = client.post(
            f"{PREFIX}/request_email", json={"email": "confirmed@ex.com"}
        )
        assert resp2.status_code == 200


# --- FORGOT PASSWORD BRANCHES (Lines 199-205) ---


@pytest.mark.asyncio
async def test_forgot_password_user_exists_logic(client):
    """Coverage for background task trigger in forgot_password (Lines 199-205)"""
    with patch(
        "src.api.auth.UserService.get_user_by_email", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = MagicMock(email="test@ex.com", username="test")

        response = client.post(
            f"{PREFIX}/forgot_password", json={"email": "test@ex.com"}
        )
        assert response.status_code == 200
        assert "instructions" in response.json()["message"]


# --- RESET PASSWORD BRANCHES (Lines 233-248) ---


@pytest.mark.asyncio
async def test_reset_password_user_not_found_logic(client):
    """Coverage for missing user in reset_password flow (Lines 233-248)"""
    with patch(
        "src.api.auth.get_email_from_token", new_callable=AsyncMock
    ) as mock_token:
        with patch(
            "src.api.auth.UserService.get_user_by_email", new_callable=AsyncMock
        ) as mock_user:
            mock_token.return_value = "ghost@ex.com"
            mock_user.return_value = None  # User is not in DB

            # Use a password that satisfies Pydantic validation (e.g., 8+ characters)
            response = client.post(
                f"{PREFIX}/reset_password/valid_format_token_here",
                json={"new_password": "StrongPassword123!"},
            )

            # Now it should bypass 422 and hit your manual 400 raise
            assert response.status_code == 400
            assert "not found" in response.json()["detail"].lower()
