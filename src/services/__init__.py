"""
Services module for business logic and external integrations.

This module contains all service classes that handle business logic
between API endpoints and repositories including authentication, email,
file uploads, and user management.
"""

from .auth import Hash, create_access_token, create_email_token, get_email_from_token, get_current_user, get_current_admin_user
from .email import send_admin_alert, _send_email_base, send_verification_email, send_reset_password_email
from .upload_file import UploadFileService
from .users import UserService

__all__ = [
    "Hash",
    "create_access_token",
    "create_email_token",
    "get_email_from_token",
    "get_current_user",
    "get_current_admin_user",
    "send_admin_alert",
    "_send_email_base",
    "send_verification_email",
    "send_reset_password_email",
    "UploadFileService",
    "UserService"
]
