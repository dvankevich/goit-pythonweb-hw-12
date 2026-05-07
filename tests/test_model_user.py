import pytest
from datetime import datetime
from src.models.user import User, UserRole


def test_user_repr():
    # Test __repr__ method (line 69 in missing list)
    user = User(id=1, username="testuser", email="test@example.com")
    expected_repr = "<User(id=1, username='testuser', email='test@example.com')>"
    assert repr(user) == expected_repr


def test_user_is_admin():
    # Test is_admin method (lines 93-98)
    user = User(role=UserRole.USER)
    assert user.is_admin() is False

    admin = User(role=UserRole.ADMIN)
    assert admin.is_admin() is True


def test_user_is_confirmed():
    # Test is_confirmed method (lines 101-106)
    user = User(confirmed=False)
    assert user.is_confirmed() is False

    user.confirmed = True
    assert user.is_confirmed() is True


def test_user_to_dict():
    # Test to_dict method (lines 77-91)
    now = datetime.now()
    user = User(
        id=1,
        username="john_doe",
        email="john@example.com",
        avatar="http://example.com/avatar.png",
        created_at=now,
        confirmed=True,
        role=UserRole.ADMIN,
    )
    data = user.to_dict()
    assert data["id"] == 1
    assert data["username"] == "john_doe"
    assert data["role"] == "admin"
    assert data["created_at"] == now.isoformat()
    assert "hashed_password" not in data  # Security check


def test_user_update_from_dict_success():
    # Test successful update_from_dict (lines 113-126)
    user = User(username="old_name", role=UserRole.USER)
    update_data = {"username": "new_name", "role": "admin", "confirmed": True}
    user.update_from_dict(update_data)
    assert user.username == "new_name"
    assert user.role == UserRole.ADMIN
    assert user.confirmed is True


def test_user_update_from_dict_invalid_field():
    # Test update_from_dict with invalid keys
    user = User()
    with pytest.raises(ValueError) as exc:
        user.update_from_dict({"password": "should_be_hashed_separately"})
    assert "Invalid fields" in str(exc.value)


def test_user_update_from_dict_invalid_role():
    # Test update_from_dict with bad role string
    user = User()
    with pytest.raises(ValueError) as exc:
        user.update_from_dict({"role": "superman"})
    assert "Invalid role value" in str(exc.value)


def test_user_create_from_dict_success():
    # Test successful create_from_dict (lines 143-165)
    data = {
        "username": "hero",
        "email": "hero@example.com",
        "hashed_password": "hashed_string_123",
        "role": "admin",
        "confirmed": True,
    }
    user = User.create_from_dict(data)
    assert user.username == "hero"
    assert user.role == UserRole.ADMIN
    assert user.confirmed is True


def test_user_create_from_dict_missing_fields():
    # Test create_from_dict with missing required fields
    with pytest.raises(ValueError) as exc:
        User.create_from_dict({"username": "no_email"})
    assert "Missing required fields" in str(exc.value)


def test_user_create_from_dict_invalid_role():
    # Test create_from_dict with invalid role
    data = {
        "username": "a",
        "email": "b@b.com",
        "hashed_password": "1",
        "role": "invalid",
    }
    with pytest.raises(ValueError) as exc:
        User.create_from_dict(data)
    assert "Invalid role value" in str(exc.value)


def test_user_create_from_dict_with_enum_object():
    # Test create_from_dict when role is already an Enum object
    data = {
        "username": "a",
        "email": "b@b.com",
        "hashed_password": "1",
        "role": UserRole.ADMIN,
    }
    user = User.create_from_dict(data)
    assert user.role == UserRole.ADMIN
