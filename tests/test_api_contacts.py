import pytest

# Basic test data for contacts
contact_data = {
    "first_name": "Taras",
    "last_name": "Shevchenko",
    "email": "taras@example.com",
    "phone": "+380123456789",
    "birthday": "1814-03-09",
}

contact_data_2 = {
    "first_name": "Lesya",
    "last_name": "Ukrainka",
    "email": "lesya@example.com",
    "phone": "+380987654321",
    "birthday": "1871-02-25",
}

PREFIX = "/api/contacts"


def test_create_contact_success(client, get_token):
    """Check successful contact creation"""
    response = client.post(
        f"{PREFIX}/",
        json=contact_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["first_name"] == contact_data["first_name"]
    assert data["email"] == contact_data["email"]
    assert "id" in data


def test_create_contact_conflict(client, get_token):
    """Check conflict: attempt to create contact with existing email"""
    # Try to add the same contact again
    response = client.post(
        f"{PREFIX}/",
        json=contact_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 409, response.text
    data = response.json()
    assert "already exists" in data["detail"]


def test_read_contacts_list(client, get_token):
    """Check getting list of contacts"""
    response = client.get(
        f"{PREFIX}/", headers={"Authorization": f"Bearer {get_token}"}
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    # Should be at least 1 contact that we created in the first test
    assert len(data) > 0
    assert data[0]["email"] == contact_data["email"]


def test_read_contact_by_id(client, get_token):
    """Check getting specific contact by ID"""
    response = client.get(
        f"{PREFIX}/1",  # ID of first created contact
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == 1
    assert data["email"] == contact_data["email"]


def test_read_contact_not_found(client, get_token):
    """Check 404 error for non-existent contact"""
    response = client.get(
        f"{PREFIX}/9999", headers={"Authorization": f"Bearer {get_token}"}
    )

    assert response.status_code == 404, response.text


def test_update_contact_success(client, get_token):
    """Check successful contact update"""
    update_data = {"first_name": "Taras (Updated)", "email": contact_data["email"]}

    response = client.put(
        f"{PREFIX}/1",
        json=update_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == "Taras (Updated)"
    assert data["email"] == contact_data["email"]


def test_update_contact_conflict(client, get_token):
    """Check conflict on update: email already taken by another contact"""
    # 1. First create second contact
    client.post(
        f"{PREFIX}/",
        json=contact_data_2,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    # 2. Try to update second contact (ID=2), specifying email of first contact
    update_data = {"email": contact_data["email"]}

    response = client.put(
        f"{PREFIX}/2",
        json=update_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 409, response.text
    data = response.json()
    assert "already taken by another of your contacts" in data["detail"]


def test_delete_contact_success(client, get_token):
    """Check successful contact deletion"""
    response = client.delete(
        f"{PREFIX}/1", headers={"Authorization": f"Bearer {get_token}"}
    )

    assert response.status_code == 204
    # Make sure there is really no content
    assert response.text == ""

    # Check that it was really deleted
    check_response = client.get(
        f"{PREFIX}/1", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert check_response.status_code == 404


def test_delete_contact_not_found(client, get_token):
    """Check 404 error when trying to delete non-existent contact"""
    response = client.delete(
        f"{PREFIX}/9999", headers={"Authorization": f"Bearer {get_token}"}
    )

    assert response.status_code == 404


def test_read_contacts_with_query_params(client, get_token):
    """Check getting list of contacts with filters (Query parameters)"""
    response = client.get(
        f"{PREFIX}/?first_name=Taras&last_name=Shevchenko&email=taras@example.com&upcoming_birthdays=true",
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_update_contact_not_found(client, get_token):
    """Check 404 error when updating non-existent contact"""
    update_data = {"first_name": "Ghost"}

    response = client.put(
        f"{PREFIX}/9999",  # Non-existent ID
        json=update_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 404
    assert "Contact not found" in response.json()["detail"]
