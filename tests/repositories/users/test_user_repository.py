import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.user_repository import UserRepository
from src.models.user import User
from src.schemas.user import UserCreate


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def user_repository(mock_session):
    return UserRepository(mock_session)


@pytest.fixture
def user():
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        confirmed=False,
        avatar="old_avatar.png",
    )


@pytest.fixture
def user_create_data():
    return UserCreate(
        username="newuser", email="new@example.com", password="secretpassword"
    )


@pytest.mark.asyncio
async def test_get_user_by_id(user_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_user_by_id(user_id=1)

    assert result is not None
    assert result.id == 1
    assert result.username == "testuser"
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_email(user_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_user_by_email(email="test@example.com")

    assert result is not None
    assert result.email == "test@example.com"


@pytest.mark.asyncio
async def test_create_user(user_repository, mock_session, user_create_data):
    # Call method
    result = await user_repository.create_user(
        body=user_create_data, avatar="http://gravatar.com/img"
    )

    assert isinstance(result, User)
    assert result.username == "newuser"
    assert result.hashed_password == "secretpassword"
    assert result.avatar == "http://gravatar.com/img"

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_confirmed_email(user_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    await user_repository.confirmed_email(email="test@example.com")

    assert user.confirmed is True
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.repositories.user_repository.invalidate_cache")
async def test_update_avatar_url(
    mock_invalidate_cache, user_repository, mock_session, user
):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.update_avatar_url(
        email="test@example.com", url="new_url.png"
    )

    assert result.avatar == "new_url.png"
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(user)
    mock_invalidate_cache.assert_awaited_once_with(f"user:{user.username}")


@pytest.mark.asyncio
async def test_update_avatar_url_not_found(user_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc:
        await user_repository.update_avatar_url(email="unknown@example.com", url="url")

    assert exc.value.status_code == 404
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_password(user_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    await user_repository.update_password(
        email="test@example.com", new_hashed_password="new_hashed_password"
    )

    assert user.hashed_password == "new_hashed_password"
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirmed_email_not_found(user_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    await user_repository.confirmed_email(email="nonexistent@example.com")

    mock_session.commit.assert_not_called()
