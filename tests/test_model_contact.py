import pytest
from datetime import date
from src.models.contact import Contact


def test_contact_repr():
    # Test __repr__ method (line 55)
    contact = Contact(
        id=1, first_name="John", last_name="Doe", email="john@example.com"
    )
    expected_repr = "<Contact(id=1, name='John Doe', email='john@example.com')>"
    assert repr(contact) == expected_repr


def test_contact_full_name():
    # Test full_name property (lines 81-87)
    contact = Contact(first_name="  Alice  ", last_name="Smith  ")
    assert contact.full_name == "Alice Smith"


def test_contact_to_dict():
    # Test to_dict method (lines 63-81)
    birthday = date(1990, 1, 1)
    contact = Contact(
        id=10,
        user_id=1,
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        phone="123456789",
        birthday=birthday,
        additional_info="Friend",
    )
    data = contact.to_dict()
    assert data["id"] == 10
    assert data["birthday"] == "1990-01-01"
    assert data["first_name"] == "Jane"


def test_contact_update_from_dict_success():
    # Test successful update_from_dict (lines 87-111)
    contact = Contact(first_name="Old", last_name="Name")
    update_data = {
        "first_name": "New",
        "birthday": "2000-05-15",
        "additional_info": "Updated info",
    }
    contact.update_from_dict(update_data)
    assert contact.first_name == "New"
    assert contact.birthday == date(2000, 5, 15)
    assert contact.additional_info == "Updated info"


def test_contact_update_from_dict_invalid_field():
    # Test update_from_dict with invalid keys (lines 102-104)
    contact = Contact()
    with pytest.raises(ValueError) as exc:
        contact.update_from_dict({"invalid_key": "value"})
    assert "Invalid fields" in str(exc.value)


def test_contact_update_from_dict_invalid_date():
    # Test update_from_dict with bad date format (lines 106-111)
    contact = Contact()
    with pytest.raises(ValueError) as exc:
        contact.update_from_dict({"birthday": "not-a-date"})
    assert "Invalid date format" in str(exc.value)


def test_contact_create_from_dict_success():
    # Test successful create_from_dict (lines 128-152)
    data = {
        "user_id": 1,
        "first_name": "Bob",
        "last_name": "Marley",
        "email": "bob@example.com",
        "phone": "555-555",
        "birthday": "1945-02-06",
        "additional_info": "Reggae legend",
    }
    contact = Contact.create_from_dict(data)
    assert contact.user_id == 1
    assert contact.first_name == "Bob"
    assert contact.birthday == date(1945, 2, 6)


def test_contact_create_from_dict_missing_fields():
    # Test create_from_dict with missing required fields (lines 139-141)
    with pytest.raises(ValueError) as exc:
        Contact.create_from_dict({"user_id": 1})
    assert "Missing required fields" in str(exc.value)


def test_contact_create_from_dict_invalid_date():
    # Test create_from_dict with invalid date format (lines 145-150)
    data = {
        "user_id": 1,
        "first_name": "A",
        "last_name": "B",
        "email": "e@e.com",
        "phone": "1",
        "birthday": "wrong-date",
    }
    with pytest.raises(ValueError) as exc:
        Contact.create_from_dict(data)
    assert "Invalid date format" in str(exc.value)


def test_contact_create_from_dict_with_date_object():
    # Test create_from_dict when birthday is already a date object (line 151-152)
    b_day = date(1995, 10, 10)
    data = {
        "user_id": 1,
        "first_name": "A",
        "last_name": "B",
        "email": "e@e.com",
        "phone": "1",
        "birthday": b_day,
    }
    contact = Contact.create_from_dict(data)
    assert contact.birthday == b_day
