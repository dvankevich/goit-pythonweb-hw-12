"""Contact repository CRUD tests."""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Contact
from src.schemas.contact import ContactCreate, ContactUpdate
from src.repositories.contact_repository import (
    get_by_id,
    get_by_email,
    create,
    update,
    delete,
)


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def test_contact():
    return Contact(
        id=1,
        first_name="Ivan",
        last_name="Ivanov",
        email="ivan@example.com",
        birthday=date(1990, 5, 10),
        user_id=1,
    )


async def test_get_by_id(mock_session, test_contact):
    """Test getting contact by ID."""
    with patch('src.repositories.contact_repository.get_by_id') as mock_get:
        mock_get.return_value = test_contact
        
        result = await get_by_id(mock_session, 1, user_id=1)
        
        assert result.first_name == "Ivan"
        assert result.email == "ivan@example.com"
        mock_get.assert_called_once_with(mock_session, 1, user_id=1)


async def test_get_by_email(mock_session, test_contact):
    """Test getting contact by email."""
    with patch('src.repositories.contact_repository.get_by_email') as mock_get:
        mock_get.return_value = test_contact
        
        result = await get_by_email(mock_session, "ivan@example.com", user_id=1)
        
        assert result.email == "ivan@example.com"
        assert result.first_name == "Ivan"
        mock_get.assert_called_once_with(mock_session, "ivan@example.com", user_id=1)


async def test_create_contact(mock_session):
    """Test creating a new contact."""
    contact_data = ContactCreate(
        first_name="Petro",
        last_name="Petrenko",
        email="petro@example.com",
        phone="+380501234567",
        birthday=date(1985, 3, 15),
    )
    
    created_contact = Contact(
        id=2,
        first_name="Petro",
        last_name="Petrenko",
        email="petro@example.com",
        phone="+380501234567",
        birthday=date(1985, 3, 15),
        user_id=1,
    )
    
    with patch('src.repositories.contact_repository.create') as mock_create:
        mock_create.return_value = created_contact
        
        result = await create(mock_session, contact_data, user_id=1)
        
        assert result.first_name == "Petro"
        assert result.email == "petro@example.com"
        assert result.id == 2
        mock_create.assert_called_once_with(mock_session, contact_data, user_id=1)


async def test_update_contact_success(mock_session, test_contact):
    """Test successful contact update."""
    update_data = ContactUpdate(
        first_name="Ivan Updated",
        phone="+380509876543"
    )
    
    updated_contact = Contact(
        id=1,
        first_name="Ivan Updated",
        last_name="Ivanov",
        email="ivan@example.com",
        phone="+380509876543",
        birthday=date(1990, 5, 10),
        user_id=1,
    )
    
    with patch('src.repositories.contact_repository.update') as mock_update:
        mock_update.return_value = updated_contact
        
        result = await update(mock_session, 1, update_data, user_id=1)
        
        assert result.first_name == "Ivan Updated"
        assert result.phone == "+380509876543"
        mock_update.assert_called_once_with(mock_session, 1, update_data, user_id=1)


async def test_update_contact_not_found(mock_session):
    """Test updating non-existent contact."""
    update_data = ContactUpdate(first_name="Updated")
    
    with patch('src.repositories.contact_repository.update') as mock_update:
        mock_update.return_value = None
        
        result = await update(mock_session, 999, update_data, user_id=1)
        
        assert result is None
        mock_update.assert_called_once_with(mock_session, 999, update_data, user_id=1)


async def test_delete_contact_success(mock_session, test_contact):
    """Test successful contact deletion."""
    with patch('src.repositories.contact_repository.delete') as mock_delete:
        mock_delete.return_value = True
        
        result = await delete(mock_session, 1, user_id=1)
        
        assert result is True
        mock_delete.assert_called_once_with(mock_session, 1, user_id=1)


async def test_delete_contact_not_found(mock_session):
    """Test deleting non-existent contact."""
    with patch('src.repositories.contact_repository.delete') as mock_delete:
        mock_delete.return_value = False
        
        result = await delete(mock_session, 999, user_id=1)
        
        assert result is False
        mock_delete.assert_called_once_with(mock_session, 999, user_id=1)
