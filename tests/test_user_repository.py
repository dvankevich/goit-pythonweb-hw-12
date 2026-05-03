import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.user_repository import UserRepository
from src.models import User
from src.schemas.user import UserCreate


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def user_repo(mock_session):
    return UserRepository(session=mock_session)


@pytest.fixture
def user_create_data():
    return UserCreate(
        username="dima_dev", email="dima@example.com", password="supersecretpassword"
    )


@pytest.fixture
def mock_user():
    return User(
        id=1,
        username="dima_dev",
        email="dima@example.com",
        hashed_password="hashed",
        confirmed=False,
    )


# ==========================================
# Тестування базових Read-методів
# ==========================================


@pytest.mark.asyncio
async def test_get_user_by_id(user_repo, mock_session, mock_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    user = await user_repo.get_user_by_id(1)

    assert user == mock_user
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_email(user_repo, mock_session, mock_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    user = await user_repo.get_user_by_email("dima@example.com")

    assert user == mock_user


# ==========================================
# Тестування Create-логіки
# ==========================================


@pytest.mark.asyncio
async def test_create_user(user_repo, mock_session, user_create_data):
    # Викликаємо метод
    created_user = await user_repo.create_user(body=user_create_data, avatar="url")

    # Перевіряємо мапінг полів (password -> hashed_password)
    assert created_user.username == "dima_dev"
    # для цього тесту це нормально. хешування виконується в api/auth.py
    # тут йде перевірка того що було передано в body.password
    assert created_user.hashed_password == "supersecretpassword"
    assert created_user.avatar == "url"

    # Перевіряємо виклики БД
    mock_session.add.assert_called_once_with(created_user)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(created_user)


# ==========================================
# Тестування Update-логіки та бізнес-правил
# ==========================================


@pytest.mark.asyncio
async def test_confirmed_email_success(user_repo, mock_session, mock_user):
    # Підмінюємо внутрішній метод get_user_by_email, щоб не мокати session.execute
    with patch.object(user_repo, "get_user_by_email", return_value=mock_user):
        await user_repo.confirmed_email("dima@example.com")

        assert mock_user.confirmed is True
        mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirmed_email_not_found(user_repo, mock_session):
    with patch.object(user_repo, "get_user_by_email", return_value=None):
        await user_repo.confirmed_email("unknown@example.com")

        # Перевіряємо, що commit не викликався, якщо юзера немає
        mock_session.commit.assert_not_called()


# Тестування Redis та помилок
@pytest.mark.asyncio
@patch("src.repositories.user_repository.invalidate_cache")  # Мокаємо Redis клієнт
async def test_update_avatar_url_success(
    mock_invalidate_cache, user_repo, mock_session, mock_user
):
    with patch.object(user_repo, "get_user_by_email", return_value=mock_user):
        updated_user = await user_repo.update_avatar_url(
            "dima@example.com", "new_avatar.png"
        )

        assert updated_user.avatar == "new_avatar.png"
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once_with(mock_user)
        # Перевіряємо, чи викликався скид кешу з правильним ключем
        mock_invalidate_cache.assert_awaited_once_with("user:dima_dev")


@pytest.mark.asyncio
async def test_update_avatar_url_not_found(user_repo, mock_session):
    with patch.object(user_repo, "get_user_by_email", return_value=None):
        # Перевіряємо, чи генерується 404 помилка FastAPI
        with pytest.raises(HTTPException) as exc_info:
            await user_repo.update_avatar_url("unknown@example.com", "url")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"
        mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_password(user_repo, mock_session, mock_user):
    with patch.object(user_repo, "get_user_by_email", return_value=mock_user):
        await user_repo.update_password("dima@example.com", "new_hashed_pwd")

        assert mock_user.hashed_password == "new_hashed_pwd"
        mock_session.commit.assert_awaited_once()
