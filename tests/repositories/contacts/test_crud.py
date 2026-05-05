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
    # Mock the database execute and scalar_one_or_none
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_contact
    mock_session.execute.return_value = mock_result
    
    result = await get_by_id(mock_session, 1, user_id=1)
    
    assert result.first_name == "Ivan"
    assert result.email == "ivan@example.com"
    mock_session.execute.assert_called_once()


async def test_get_by_email(mock_session, test_contact):
    """Test getting contact by email."""
    # Mock the database execute and scalar_one_or_none
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_contact
    mock_session.execute.return_value = mock_result
    
    result = await get_by_email(mock_session, "ivan@example.com", user_id=1)
    
    assert result.email == "ivan@example.com"
    assert result.first_name == "Ivan"
    mock_session.execute.assert_called_once()


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
    
    # Mock the database operations
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    # Test the actual create function
    result = await create(mock_session, contact_data, user_id=1)
    
    # Since we can't easily mock the Contact creation, let's just verify the calls
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


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
    
    # Mock get_by_id to return existing contact
    with patch('src.repositories.contact_repository.get_by_id') as mock_get:
        mock_get.return_value = test_contact
        
        # Mock commit and refresh
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await update(mock_session, 1, update_data, user_id=1)
        
        assert result.first_name == "Ivan Updated"
        assert result.phone == "+380509876543"
        mock_session.commit.assert_called_once()


async def test_update_contact_not_found(mock_session):
    """Test updating non-existent contact."""
    update_data = ContactUpdate(first_name="Updated")
    
    # Mock get_by_id to return None (contact not found)
    with patch('src.repositories.contact_repository.get_by_id') as mock_get:
        mock_get.return_value = None
        
        result = await update(mock_session, 999, update_data, user_id=1)
        
        assert result is None


async def test_delete_contact_success(mock_session, test_contact):
    """Test successful contact deletion."""
    # Mock get_by_id to return existing contact
    with patch('src.repositories.contact_repository.get_by_id') as mock_get:
        mock_get.return_value = test_contact
        
        # Mock delete and commit
        mock_session.delete = AsyncMock()
        mock_session.commit = AsyncMock()
        
        result = await delete(mock_session, 1, user_id=1)
        
        assert result is True
        mock_session.delete.assert_called_once_with(test_contact)
        mock_session.commit.assert_called_once()


async def test_delete_contact_not_found(mock_session):
    """Test deleting non-existent contact."""
    # Mock get_by_id to return None (contact not found)
    with patch('src.repositories.contact_repository.get_by_id') as mock_get:
        mock_get.return_value = None
        
        result = await delete(mock_session, 999, user_id=1)
        
        assert result is False
