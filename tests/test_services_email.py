import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi_mail.errors import ConnectionErrors
from fastapi_mail import MessageType
from src.services.email import send_verification_email, send_reset_password_email


@pytest.fixture
def mock_fastmail():
    with patch("src.services.email.FastMail") as mock:
        fm_instance = mock.return_value
        fm_instance.send_message = AsyncMock()
        yield fm_instance


# Fixture so tests always think HTML templates exist
@pytest.fixture
def mock_templates_exist():
    with patch("src.services.email.Path.exists") as mock_exists:
        mock_exists.return_value = True
        yield mock_exists


@pytest.mark.asyncio
async def test_send_email_success(mock_fastmail, mock_templates_exist):
    """Test of successful email sending for confirmation"""
    email = "test@example.com"
    username = "testuser"
    host = "http://localhost:8000"

    with patch("src.services.email.create_email_token") as mock_token:
        mock_token.return_value = "fake_token_123"

        await send_verification_email(email, username, host)

        assert mock_fastmail.send_message.called

        # Get call arguments
        args, kwargs = mock_fastmail.send_message.call_args
        message = args[0]
        template_name = kwargs.get("template_name")

        assert message.subject == "Confirm your email address"
        assert message.recipients[0].email == email
        assert template_name == "verify_email.html"


@pytest.mark.asyncio
async def test_send_reset_password_email_success(mock_fastmail, mock_templates_exist):
    """Test of successful email sending for password reset"""
    email = "reset@example.com"
    username = "resetuser"
    host = "http://localhost:8000"

    await send_reset_password_email(email, username, host)

    assert mock_fastmail.send_message.called

    args, kwargs = mock_fastmail.send_message.call_args
    message = args[0]
    template_name = kwargs.get("template_name")

    assert message.subject == "Password Reset Request"
    assert message.recipients[0].email == email
    assert template_name == "reset_password.html"


@pytest.mark.asyncio
async def test_send_email_fallback_flow(mock_fastmail):
    """Separate test to check Fallback logging (when template not found)"""
    email = "fallback@example.com"

    with patch("src.services.email.Path.exists", return_value=False):
        # Use AsyncMock for admin notification
        with patch(
            "src.services.email.send_admin_alert", new_callable=AsyncMock
        ) as mock_admin:
            await send_verification_email(email, "user", "host")

    assert mock_fastmail.send_message.called
    message = mock_fastmail.send_message.call_args[0][0]

    assert "Security Link" in message.subject
    assert message.subtype == MessageType.plain
