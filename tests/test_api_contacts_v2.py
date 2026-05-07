import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status
from main import app
from src.services.auth import get_current_user
from src.models.user import User

# --- Mocks and Setup ---


@pytest.fixture
def mock_user():
    """Create a mock user for dependency injection"""
    return User(id=1, username="test_user", email="test@example.com", confirmed=True)


@pytest.fixture
def authenticated_client(client, mock_user):
    """Override get_current_user to bypass real authentication"""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield client
    app.dependency_overrides.clear()


# --- Extended Tests for Coverage ---


@pytest.mark.asyncio
async def test_create_contact_conflict_branch(authenticated_client, mock_user):
    """Coverage for lines 36-42 (Conflict when email exists)"""
    with patch(
        "src.api.contact_api.contact_repository.get_by_email", new_callable=AsyncMock
    ) as mock_get:
        # Simulate that contact with this email ALREADY exists
        mock_get.return_value = AsyncMock(id=1, email="dup@ex.com")

        response = authenticated_client.post(
            "/api/contacts/",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "dup@ex.com",
                "phone": "123",
                "birthday": "1990-01-01",
            },
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_read_contact_not_found_branch(authenticated_client):
    """Coverage for lines 102-106 (404 Not Found)"""
    with patch(
        "src.api.contact_api.contact_repository.get_by_id", new_callable=AsyncMock
    ) as mock_get:
        # Simulate contact NOT found
        mock_get.return_value = None

        response = authenticated_client.get("/api/contacts/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_contact_email_conflict_branch(authenticated_client, mock_user):
    """Coverage for lines 135-136 (Email taken by ANOTHER contact)"""
    with patch(
        "src.api.contact_api.contact_repository.get_by_email", new_callable=AsyncMock
    ) as mock_get:
        # Simulate that email belongs to contact with ID 55, while we update ID 10
        existing_contact = AsyncMock()
        existing_contact.id = 55
        mock_get.return_value = existing_contact

        response = authenticated_client.put(
            "/api/contacts/10", json={"email": "taken@ex.com"}
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already taken" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_contact_not_found_branch(authenticated_client):
    """Coverage for lines 145-151 (404 Not Found on update)"""
    with patch(
        "src.api.contact_api.contact_repository.get_by_email", new_callable=AsyncMock
    ) as mock_email:
        with patch(
            "src.api.contact_api.contact_repository.update", new_callable=AsyncMock
        ) as mock_upd:
            mock_email.return_value = None
            mock_upd.return_value = None  # Repository returns None if not found

            response = authenticated_client.put(
                "/api/contacts/999", json={"first_name": "New"}
            )
            assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_contact_not_found_branch(authenticated_client):
    """Coverage for lines 175-181 (404 Not Found on delete)"""
    with patch(
        "src.api.contact_api.contact_repository.delete", new_callable=AsyncMock
    ) as mock_del:
        # Simulate repository returning False (failed to delete)
        mock_del.return_value = False

        response = authenticated_client.delete("/api/contacts/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
