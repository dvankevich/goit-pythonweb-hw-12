import pytest
from unittest.mock import AsyncMock, patch

from src.services.users import UserService
from src.schemas.user import UserCreate

# ====================== FIXTURES ======================


@pytest.fixture
def user_service(mock_session):
    """Creates service instance with isolated (mocked) repository"""
    service = UserService(mock_session)
    # Replace repository with mock to test only calls, not DB
    service.repository = AsyncMock()
    return service


@pytest.fixture
def user_create_data():
    return UserCreate(
        username="test_dev", email="dev@example.com", password="secretpassword"
    )


# ====================== TESTS FOR CREATE USER (Gravatar) ======================


@pytest.mark.asyncio
@patch("src.services.users.Gravatar")
async def test_create_user_gravatar_success(
    mock_gravatar_class, user_service, user_create_data
):
    # Gravatar mock returns fake URL
    mock_gravatar_instance = mock_gravatar_class.return_value
    mock_gravatar_instance.get_image.return_value = "http://gravatar.com/avatar/123"

    await user_service.create_user(user_create_data)

    user_service.repository.create_user.assert_called_once_with(
        user_create_data, "http://gravatar.com/avatar/123"
    )


@pytest.mark.asyncio
@patch("src.services.users.Gravatar")
async def test_create_user_gravatar_error(
    mock_gravatar_class, user_service, user_create_data
):
    # Network error occurred
    mock_gravatar_instance = mock_gravatar_class.return_value
    mock_gravatar_instance.get_image.side_effect = Exception("Gravatar API is down")

    await user_service.create_user(user_create_data)

    # check that error was caught with avatar=None
    user_service.repository.create_user.assert_called_once_with(user_create_data, None)


# ====================== TESTS FOR DELEGATED METHODS ======================


@pytest.mark.asyncio
async def test_get_user_by_id(user_service):
    await user_service.get_user_by_id(1)
    user_service.repository.get_user_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_user_by_username(user_service):
    await user_service.get_user_by_username("test_dev")
    user_service.repository.get_user_by_username.assert_called_once_with("test_dev")


@pytest.mark.asyncio
async def test_get_user_by_email(user_service):
    await user_service.get_user_by_email("dev@example.com")
    user_service.repository.get_user_by_email.assert_called_once_with("dev@example.com")


@pytest.mark.asyncio
async def test_confirmed_email(user_service):
    await user_service.confirmed_email("dev@example.com")
    user_service.repository.confirmed_email.assert_called_once_with("dev@example.com")


@pytest.mark.asyncio
async def test_update_avatar_url(user_service):
    await user_service.update_avatar_url("dev@example.com", "http://new.avatar/url")
    user_service.repository.update_avatar_url.assert_called_once_with(
        "dev@example.com", "http://new.avatar/url"
    )


# @pytest.mark.asyncio
# async def test_update_avatar(user_service):
#     await user_service.update_avatar("dev@example.com", "http://new.avatar/url")
#     user_service.repository.update_avatar_url.assert_called_once_with(
#         "dev@example.com", "http://new.avatar/url"
#     )


@pytest.mark.asyncio
async def test_update_password(user_service):
    await user_service.update_password("dev@example.com", "new_hashed_password")
    user_service.repository.update_password.assert_called_once_with(
        "dev@example.com", "new_hashed_password"
    )
