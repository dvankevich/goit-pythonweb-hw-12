# pytest --cov=src.utils.create_admin --cov-report=term-missing tests/test_utils_create_admin.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.create_admin import create_admin as create_admin_user
from src.models.user import User, UserRole


@pytest.mark.asyncio
async def test_create_admin_user_already_exists():
    """Test: Admin already exists in the database (the code should simply exit)"""
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    # Simulate scalar_one_or_none returning an existing user
    mock_result.scalar_one_or_none.return_value = User(username="admin")
    mock_db.execute.return_value = mock_result

    # Mock get_db as an asynchronous generator
    async def mock_get_db():
        yield mock_db

    with patch("src.utils.create_admin.get_db", side_effect=mock_get_db):
        with patch("src.utils.create_admin.settings") as mock_settings:
            mock_settings.ADMIN_EMAIL = "admin@example.com"
            mock_settings.ADMIN_USERNAME = "admin"

            await create_admin_user()

    # Verify that db.add was NOT called
    mock_db.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_admin_user_success():
    """Test: Successful creation of a new admin"""
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    # Simulate that the user does not exist
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    async def mock_get_db():
        yield mock_db

    with patch("src.utils.create_admin.get_db", side_effect=mock_get_db):
        with patch("src.utils.create_admin.settings") as mock_settings:
            mock_settings.ADMIN_EMAIL = "new_admin@example.com"
            mock_settings.ADMIN_USERNAME = "new_admin"
            mock_settings.ADMIN_PASSWORD.get_secret_value.return_value = "password"

            with patch("src.utils.create_admin.Hash") as mock_hash:
                mock_hash.return_value.get_password_hash.return_value = (
                    "hashed_password"
                )

                await create_admin_user()

    # Verify the creation logic
    assert mock_db.add.called
    created_user = mock_db.add.call_args[0][0]
    assert created_user.username == "new_admin"
    assert created_user.role == UserRole.ADMIN
    assert mock_db.commit.called
    assert mock_db.refresh.called


@pytest.mark.asyncio
async def test_create_admin_user_exception():
    """Test: Error during commit (should trigger rollback)"""
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    # Simulate an exception during commit
    mock_db.commit.side_effect = Exception("DB Error")

    async def mock_get_db():
        yield mock_db

    with patch("src.utils.create_admin.get_db", side_effect=mock_get_db):
        with patch("src.utils.create_admin.settings"):
            with patch("src.utils.create_admin.Hash"):
                await create_admin_user()

    # Verify that rollback was called
    assert mock_db.rollback.called
