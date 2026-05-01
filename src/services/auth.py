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
from src.models.user import User


class Hash:
    def verify_password(self, plain_password: str, hashed_password: str):
        password_byte = plain_password.encode("utf-8")
        hashed_byte = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_byte, hashed_byte)

    def get_password_hash(self, password: str):
        # Обрізаємо до 72 байт для безпеки bcrypt
        password_byte = password.encode("utf-8")[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password_byte, salt).decode("utf-8")

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ====================== JWT TOKENS ======================


async def create_access_token(data: dict, expires_delta: Optional[int] = None):
    """Створення access токена для авторизації"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + timedelta(seconds=expires_delta)
    else:
        expire = datetime.now(UTC) + timedelta(seconds=settings.JWT_EXPIRATION_SECONDS)

    to_encode.update({"exp": expire})

    # Важливо: розпаковуємо SecretStr в звичайний рядок
    secret_key = settings.JWT_SECRET.get_secret_value()

    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_email_token(data: dict):
    """Створення токена для підтвердження email"""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})

    # Розпаковуємо SecretStr
    secret_key = settings.JWT_SECRET.get_secret_value()

    token = jwt.encode(to_encode, secret_key, algorithm=settings.JWT_ALGORITHM)
    return token


async def get_email_from_token(token: str):
    """Отримання email з токена підтвердження"""
    try:
        secret_key = settings.JWT_SECRET.get_secret_value()

        payload = jwt.decode(token, secret_key, algorithms=[settings.JWT_ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Неправильний токен для перевірки електронної пошти",
            )
        return email
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Неправильний токен для перевірки електронної пошти",
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
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

    # 1. Спроба отримати користувача з кешу Redis
    if settings.ENABLE_REDIS:
        try:
            cached_user = await redis_client.get(f"user:{username}")
            if cached_user:
                logger.debug(f"User '{username}' retrieved from Redis cache.")
                user_data = json.loads(cached_user)
                if user_data.get("created_at"):
                    user_data["created_at"] = datetime.fromisoformat(user_data["created_at"])
                return User(**user_data)
            # Логуємо випадок, коли кеш увімкнено, але ключа немає (Cache Miss)
            logger.debug(f"User '{username}' not found in Redis cache (Cache Miss).")

        except Exception as e:
            logger.warning(f"Redis error: {e}. Falling back to PostgreSQL.")

    # Якщо Redis вимкнено або сталася помилка — йдемо в БД
    logger.debug(f"Retrieving user '{username}' from PostgreSQL database.")
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    
    if user is None:
        raise credentials_exception

    # Зберігаємо в кеш тільки якщо він увімкнений
    if settings.ENABLE_REDIS:
        try:
            user_to_cache = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar": user.avatar,
                "confirmed": user.confirmed,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "hashed_password": user.hashed_password
            }
            await redis_client.set(f"user:{username}", json.dumps(user_to_cache), ex=3600)
            logger.debug(f"User '{username}' data has been cached in Redis.")
        except Exception as e:
            logger.error(f"Failed to cache user: {e}")

    return user
