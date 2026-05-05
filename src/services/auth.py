import bcrypt
import json
import logging

from datetime import datetime, timedelta, UTC
from typing import Optional

from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from src.db.session import get_db
from src.db.redis_client import redis_client
from src.config.app_config import settings
from src.services.users import UserService
from src.models.user import User, UserRole


class Hash:
    """Utility class for password hashing and verification.
    
    Provides methods to hash passwords using bcrypt and verify
    password hashes against plain text passwords.
    """
    def verify_password(self, plain_password: str, hashed_password: str):
        """Verify a plain password against a hashed password.
        
        Args:
            plain_password: The plain text password to verify.
            hashed_password: The bcrypt hashed password to verify against.
        
        Returns:
            bool: True if the password matches, False otherwise.
        """
        password_byte = plain_password.encode("utf-8")
        hashed_byte = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_byte, hashed_byte)

    def get_password_hash(self, password: str):
        """Hash a plain text password using bcrypt.
        
        Args:
            password: The plain text password to hash.
        
        Returns:
            str: The bcrypt hashed password as a string.
        """
        # Truncate to 72 bytes for bcrypt security
        password_byte = password.encode("utf-8")[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password_byte, salt).decode("utf-8")


logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ====================== JWT TOKENS ======================


def create_access_token(data: dict, expires_delta: Optional[int] = None):
    """Create an access token for authentication.
    
    Args:
        data: Dictionary containing data to encode in token.
        expires_delta: Optional custom expiration time in seconds.
    
    Returns:
        str: JWT access token.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + timedelta(seconds=expires_delta)
    else:
        expire = datetime.now(UTC) + timedelta(seconds=settings.JWT_EXPIRATION_SECONDS)

    to_encode.update({"exp": expire})

    # Important: unpack SecretStr to regular string
    secret_key = settings.JWT_SECRET.get_secret_value()

    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_email_token(data: dict):
    """Create a token for email confirmation.
    
    Args:
        data: Dictionary containing data to encode in the token.
    
    Returns:
        str: JWT token for email confirmation.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})

    # Unpack SecretStr
    secret_key = settings.JWT_SECRET.get_secret_value()

    token = jwt.encode(to_encode, secret_key, algorithm=settings.JWT_ALGORITHM)
    return token


def get_email_from_token(token: str):
    """Extract email from email confirmation token.
    
    Args:
        token: JWT token to decode.
    
    Returns:
        str: Email address from token.
    
    Raises:
        HTTPException: If token is invalid or email is not found.
    """
    try:
        secret_key = settings.JWT_SECRET.get_secret_value()

        payload = jwt.decode(token, secret_key, algorithms=[settings.JWT_ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Invalid token for email verification",
            )
        return email
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid token for email verification",
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    """Get the current authenticated user from JWT token.
    
    Args:
        token: JWT access token from the request header.
        db: Database session dependency.
    
    Returns:
        User: The authenticated user object.
    
    Raises:
        HTTPException: If token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        secret_key = settings.JWT_SECRET.get_secret_value()
        payload = jwt.decode(token, secret_key, algorithms=[settings.JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 1. Try to get user from Redis cache
    if settings.ENABLE_REDIS:
        try:
            cached_user = await redis_client.get(f"user:{username}")
            if cached_user:
                logger.debug(f"User '{username}' found in Redis cache (Cache Hit).")
                user_data = json.loads(cached_user)
                # Add created_at timestamp if missing
                if "created_at" not in user_data:
                    user_data["created_at"] = datetime.now(UTC).isoformat()
                return User(**user_data)
        except Exception as e:
            logger.warning(f"Redis error: {e}. Falling back to PostgreSQL.")
    
    # If Redis is disabled or error occurred - go to DB
    logger.debug(f"Retrieving user '{username}' from PostgreSQL database.")
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)

    if user is None:
        raise credentials_exception

    # Save to cache only if enabled
    if settings.ENABLE_REDIS:
        try:
            user_to_cache = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar": user.avatar,
                "confirmed": user.confirmed,
                "role": user.role.value if hasattr(user.role, "value") else user.role,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "hashed_password": user.hashed_password,
            }
            await redis_client.set(
                f"user:{username}", json.dumps(user_to_cache), ex=3600
            )
            logger.debug(f"User '{username}' data has been cached in Redis.")
        except Exception as e:
            logger.error(f"Failed to cache user: {e}")

    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """Get the current user and verify they have admin privileges.
    
    Args:
        current_user: The authenticated user from get_current_user dependency.
    
    Returns:
        User: The admin user object.
    
    Raises:
        HTTPException: If user does not have admin role.
    """
    # Check if user role matches ADMIN
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges",
        )
    return current_user
