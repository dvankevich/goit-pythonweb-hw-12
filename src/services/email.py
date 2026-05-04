import logging
from pathlib import Path
from jinja2 import TemplateNotFound
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr, NameEmail

from src.services.auth import create_email_token
from src.config.app_config import settings

logger = logging.getLogger(__name__)

# Використовуємо абсолютний шлях для надійності
TEMPLATE_DIR = Path(__file__).parent / "templates"

email_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=TEMPLATE_DIR,
)


async def _send_email_base(
    email: EmailStr,
    username: str,
    subject: str,
    template_name: str,
    template_context: dict,
):
    """
    Універсальна функція для відправки імейлів.
    Централізовано обробляє помилки та перевіряє наявність шаблонів.
    """
    try:
        # Перевірка наявності файлу шаблону перед відправкою
        if not (TEMPLATE_DIR / template_name).exists():
            logger.error(f"Template '{template_name}' not found in {TEMPLATE_DIR}")
            return False

        message = MessageSchema(
            subject=subject,
            recipients=[NameEmail(name=username, email=email)],
            template_body=template_context,
            subtype=MessageType.html,
        )

        fm = FastMail(email_conf)
        await fm.send_message(message, template_name=template_name)
        logger.info(f"Email '{subject}' successfully sent to {email}")
        return True

    except ConnectionErrors as err:
        logger.error(f"Connection error while sending '{subject}' to {email}: {err}")
    except Exception as err:
        logger.error(
            f"Unexpected error sending '{subject}' to {email}: {err}", exc_info=True
        )
    return False


async def send_verification_email(email: EmailStr, username: str, host: str):
    """Відправка листа для підтвердження пошти"""
    token = create_email_token({"sub": email})
    context = {
        "host": host,
        "username": username,
        "token": token,
    }
    await _send_email_base(
        email=email,
        username=username,
        subject="Confirm your email",
        template_name="verify_email.html",
        template_context=context,
    )


async def send_reset_password_email(email: EmailStr, username: str, host: str):
    """Відправка листа для скидання пароля"""
    token = create_email_token({"sub": email})
    context = {
        "host": host,
        "username": username,
        "token": token,
    }
    await _send_email_base(
        email=email,
        username=username,
        subject="Reset your password",
        template_name="reset_password.html",
        template_context=context,
    )
