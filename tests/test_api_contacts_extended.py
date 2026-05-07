import pytest
from fastapi import status
from datetime import date, timedelta

# Assuming the prefix is defined in the router, but in tests we use the full path
PREFIX = "/api/contacts"


@pytest.mark.asyncio
async def test_create_contact_conflict(client, get_token, db_session):
    """Test creating a contact with an email that already exists (lines 36-42)"""
    # 1. Create an initial contact
    client.post(
        f"{PREFIX}/",
        json={
            "first_name": "Original",
            "last_name": "User",
            "email": "duplicate@example.com",
            "phone": "123456789",
            "birthday": "1990-01-01",
        },
        headers={"Authorization": f"Bearer {get_token}"},
    )

    # 2. Try to create another contact with the same email
    response = client.post(
        f"{PREFIX}/",
        json={
            "first_name": "New",
            "last_name": "Person",
            "email": "duplicate@example.com",
            "phone": "987654321",
            "birthday": "1995-05-05",
        },
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_read_contacts_filtering(client, get_token):
    """Test search filters and upcoming birthdays (lines 77)"""
    # Search by name
    response = client.get(
        f"{PREFIX}/?first_name=John", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200

    # Search upcoming birthdays
    response = client.get(
        f"{PREFIX}/?upcoming_birthdays=true",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_read_contact_not_found(client, get_token):
    """Test getting a non-existent contact (lines 102-106)"""
    response = client.get(
        f"{PREFIX}/99999", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_contact_not_found(client, get_token):
    """Test updating a non-existent contact (lines 145-151)"""
    response = client.put(
        f"{PREFIX}/99999",
        json={"first_name": "Updated"},
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_contact_email_conflict(client, get_token):
    """Test updating a contact's email to one already used by another contact (lines 135-136)"""
    # 1. Create contact A
    client.post(
        f"{PREFIX}/",
        json={
            "first_name": "A",
            "last_name": "User",
            "email": "a@ex.com",
            "phone": "1",
            "birthday": "1990-01-01",
        },
        headers={"Authorization": f"Bearer {get_token}"},
    )

    # 2. Create contact B
    resp_b = client.post(
        f"{PREFIX}/",
        json={
            "first_name": "B",
            "last_name": "User",
            "email": "b@ex.com",
            "phone": "2",
            "birthday": "1990-01-01",
        },
        headers={"Authorization": f"Bearer {get_token}"},
    )

    contact_b_id = resp_b.json()["id"]

    # 3. Try to update B's email to A's email
    response = client.put(
        f"{PREFIX}/{contact_b_id}",
        json={"email": "a@ex.com"},
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_contact_not_found(client, get_token):
    """Test deleting a non-existent contact (lines 175-181)"""
    response = client.delete(
        f"{PREFIX}/99999", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 404
