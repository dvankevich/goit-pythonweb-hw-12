import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock

from main import app
from src.db.session import get_db
from src.models.user import Base, User, UserRole
from src.services.auth import create_access_token, Hash
from src.config.app_config import settings

# Test SQLite in-memory database setup
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

# Test user for integration tests
test_user_data = {
    "username": "deadpool",
    "email": "deadpool@example.com",
    "password": "secretpassword",
}

# --- UNIT TEST FIXTURES ---


@pytest.fixture
def mock_session():
    """Universal session for unit testing repositories and services"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_user():
    """Basic user mock for unit testing"""
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
    """Creates tables and test user before starting module tests"""

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


@pytest.fixture
async def db_session():
    """Fixture for direct work with test database"""
    async with TestingSessionLocal() as session:
        yield session
        # After test, clear session if needed
        await session.rollback()


@pytest.fixture(scope="session")
def client():
    """Sets up TestClient and overrides database dependency"""
    from main import app
    from src.db.session import get_db

    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = False

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def get_token():
    """Generates JWT token for authorized requests in tests"""
    token = await create_access_token(data={"sub": test_user_data["username"]})
    return token


@pytest_asyncio.fixture()
async def get_admin_token():
    """Creates real admin in database and returns their token"""
    async with TestingSessionLocal() as session:
        query = select(User).filter(User.username == settings.ADMIN_USERNAME)
        result = await session.execute(query)
        admin = result.scalar_one_or_none()

        if not admin:
            hashed_password = Hash().get_password_hash(
                settings.ADMIN_PASSWORD.get_secret_value()
            )
            admin = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=hashed_password,
                role=UserRole.ADMIN,  # This is the key check
                confirmed=True,
            )
            session.add(admin)
            await session.commit()
            await session.refresh(admin)

    token = await create_access_token(data={"sub": settings.ADMIN_USERNAME})
    return token
