"""Simple email service tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi_mail import MessageType

from src.services.email import send_verification_email, send_reset_password_email


@pytest.mark.asyncio
async def test_send_verification_email_basic():
    """Test email verification sending without complex mocking."""
    email = "test@example.com"
    username = "testuser"
    host = "http://localhost:8000"
    
    # Mock FastMail to avoid actual email sending
    with patch("src.services.email.FastMail") as mock_fastmail:
        mock_fm = AsyncMock()
        mock_fastmail.return_value = mock_fm
        
        # Mock template exists to avoid file system issues
        with patch("src.services.email.Path.exists", return_value=True):
            with patch("src.services.email.create_email_token", return_value="fake_token"):
                result = await send_verification_email(email, username, host)
                
                assert result is True
                assert mock_fm.send_message.called


@pytest.mark.asyncio
async def test_send_reset_email_basic():
    """Test password reset email sending without complex mocking."""
    email = "reset@example.com"
    username = "resetuser"
    host = "http://localhost:8000"
    
    # Mock FastMail to avoid actual email sending
    with patch("src.services.email.FastMail") as mock_fastmail:
        mock_fm = AsyncMock()
        mock_fastmail.return_value = mock_fm
        
        # Mock template exists to avoid file system issues
        with patch("src.services.email.Path.exists", return_value=True):
            with patch("src.services.email.create_email_token", return_value="fake_token"):
                result = await send_reset_password_email(email, username, host)
                
                assert result is True
                assert mock_fm.send_message.called


@pytest.mark.asyncio
async def test_send_email_template_missing():
    """Test email sending when template is missing."""
    email = "test@example.com"
    username = "testuser"
    host = "http://localhost:8000"
    
    # Mock FastMail to avoid actual email sending
    with patch("src.services.email.FastMail") as mock_fastmail:
        mock_fm = AsyncMock()
        mock_fastmail.return_value = mock_fm
        
        # Mock template missing
        with patch("src.services.email.Path.exists", return_value=False):
            with patch("src.services.email.create_email_token", return_value="fake_token"):
                result = await send_verification_email(email, username, host)
                
                assert result is True
                assert mock_fm.send_message.called
                
                # Check that fallback message was sent
                call_args = mock_fm.send_message.call_args
                message = call_args[0][0]
                assert "Security Link" in message.subject
                assert message.subtype == MessageType.plain
