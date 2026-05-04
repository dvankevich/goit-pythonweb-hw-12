import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock

from main import app
from src.db.session import get_db  # Перевірте шлях до вашої залежності get_db
from src.models.user import Base, User, UserRole
from src.services.auth import create_access_token, Hash

# Налаштування тестової бази SQLite в пам'яті
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

# Тестовий користувач для інтеграційних тестів
test_user_data = {
    "username": "deadpool",
    "email": "deadpool@example.com",
    "password": "secretpassword",
}

# --- UNIT TEST FIXTURES ---


@pytest.fixture
def mock_session():
    """Універсальна сесія для модульних тестів репозиторіїв та сервісів"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user():
    """Базовий мок користувача для модульних тестів"""
    return User(
        id=1,
        username="test_user",
        email="test@example.com",
        role=UserRole.USER,
        confirmed=True,
    )


# --- INTEGRATION TEST FIXTURES ---


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    """Створює таблиці та тестового користувача перед початком тестів модуля"""

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        async with TestingSessionLocal() as session:
            hash_password = Hash().get_password_hash(test_user_data["password"])
            current_user = User(
                username=test_user_data["username"],
                email=test_user_data["email"],
                hashed_password=hash_password,
                confirmed=True,
                role=UserRole.USER,
            )
            session.add(current_user)
            await session.commit()

    asyncio.run(init_models())


@pytest.fixture(scope="module")
def client():
    """Налаштовує TestClient та перевизначає залежність БД"""

    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def get_token():
    """Генерує JWT токен для авторизованих запитів у тестах"""
    token = await create_access_token(data={"sub": test_user_data["username"]})
    return token
