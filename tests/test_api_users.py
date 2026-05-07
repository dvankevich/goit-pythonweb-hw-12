import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from main import app
from src.services.auth import get_current_admin_user
from src.config.app_config import settings

PREFIX = "/api/users"


@pytest.fixture
def mock_upload_service():
    with patch("src.api.users.UploadFileService") as mock:
        instance = mock.return_value
        instance.upload_file.return_value = "http://example.com/new_avatar.png"
        yield instance


# --- /me TESTS ---


def test_get_me_success(client, get_token):
    response = client.get(
        f"{PREFIX}/me", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "deadpool"
    assert data["email"] == "deadpool@example.com"


def test_get_me_unauthorized(client):
    response = client.get(f"{PREFIX}/me")
    assert response.status_code == 401


# --- /avatar TESTS ---


def test_update_avatar_as_regular_user_fails(client, get_token):
    file_content = b"fake image"
    files = {"file": ("avatar.png", file_content, "image/png")}

    response = client.patch(
        f"{PREFIX}/avatar",
        headers={"Authorization": f"Bearer {get_token}"},
        files=files,
    )

    assert response.status_code == 403


def test_update_avatar_as_admin_success(client, get_admin_token, mock_upload_service):
    file_content = b"real admin image"
    files = {"file": ("admin_avatar.png", file_content, "image/png")}

    response = client.patch(
        f"{PREFIX}/avatar",
        headers={"Authorization": f"Bearer {get_admin_token}"},
        files=files,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == settings.ADMIN_USERNAME
    assert data["avatar"] == "http://example.com/new_avatar.png"


def test_update_avatar_no_file(client, get_admin_token):
    # Send request without files argument
    response = client.patch(
        f"{PREFIX}/avatar", headers={"Authorization": f"Bearer {get_admin_token}"}
    )

    assert response.status_code == 422

    data = response.json()
    assert data["detail"][0]["loc"] == ["body", "file"]
    assert data["detail"][0]["msg"] == "Field required"
