import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi_mail.errors import ConnectionErrors
from src.services.email import send_verification_email, send_reset_password_email


# Створюємо фікстуру для мокання FastMail
@pytest.fixture
def mock_fastmail():
    with patch("src.services.email.FastMail") as mock:
        fm_instance = mock.return_value
        fm_instance.send_message = AsyncMock()
        yield fm_instance


@pytest.mark.asyncio
async def test_send_email_success(mock_fastmail):
    """Тест успішного надсилання листа для підтвердження (рядок 36-49)"""
    email = "test@example.com"
    username = "testuser"
    host = "http://localhost:8000"

    with patch("src.services.email.create_email_token") as mock_token:
        mock_token.return_value = "fake_token_123"

        await send_verification_email(email, username, host)

        # Перевіряємо, чи був викликаний метод send_message
        assert mock_fastmail.send_message.called

        # Отримуємо об'єкт повідомлення з виклику
        message = mock_fastmail.send_message.call_args[0][0]
        template_name = mock_fastmail.send_message.call_args[1]["template_name"]

        assert message.subject == "Confirm your email"
        assert message.recipients[0].email == email
        assert template_name == "verify_email.html"


@pytest.mark.asyncio
async def test_send_email_connection_error(mock_fastmail):
    """Тест обробки помилки з'єднання (ConnectionErrors) """
    mock_fastmail.send_message.side_effect = ConnectionErrors("Connection failed")

    # Функція не повинна кидати Exception, бо ми ловимо ConnectionErrors
    await send_verification_email("test@example.com", "user", "host")

    assert mock_fastmail.send_message.called


@pytest.mark.asyncio
async def test_send_email_unexpected_error(mock_fastmail):
    """Тест обробки непередбаченої помилки (Exception) """
    mock_fastmail.send_message.side_effect = Exception("Unexpected")

    await send_verification_email("test@example.com", "user", "host")

    assert mock_fastmail.send_message.called


@pytest.mark.asyncio
async def test_send_reset_password_email_success(mock_fastmail):
    """Тест успішного надсилання листа для скидання пароля """
    email = "reset@example.com"
    username = "resetuser"
    host = "http://localhost:8000"

    await send_reset_password_email(email, username, host)

    assert mock_fastmail.send_message.called

    message = mock_fastmail.send_message.call_args[0][0]
    template_name = mock_fastmail.send_message.call_args[1]["template_name"]

    assert message.subject == "Reset your password"
    assert message.recipients[0].email == email
    assert template_name == "reset_password.html"


@pytest.mark.asyncio
async def test_send_reset_password_email_error(mock_fastmail):
    """Тест обробки помилки при скиданні пароля """
    mock_fastmail.send_message.side_effect = Exception("Reset Error")

    await send_reset_password_email("test@example.com", "user", "host")

    assert mock_fastmail.send_message.called
