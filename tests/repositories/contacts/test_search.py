"""Contact repository search and filter tests."""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Contact
from src.repositories.contact_repository import get_all


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


async def test_get_all_no_filters(mock_session, test_contact):
    """Test getting all contacts without filters."""
    mock_contacts = [test_contact]
    
    # Mock the database execute and scalars
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = mock_contacts
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    
    result = await get_all(mock_session, user_id=1)
    
    assert len(result) == 1
    assert result[0].first_name == "Ivan"
    mock_session.execute.assert_called_once()


async def test_get_all_with_filters(mock_session, test_contact):
    """Test getting contacts with filters."""
    mock_contacts = [test_contact]
    
    # Mock the database execute and scalars
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = mock_contacts
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    
    result = await get_all(
        mock_session, 
        user_id=1,
        first_name="Ivan",
        last_name="Ivanov",
        email="ivan@example.com"
    )
    
    assert len(result) == 1
    assert result[0].first_name == "Ivan"
    assert result[0].last_name == "Ivanov"
    mock_session.execute.assert_called_once()


async def test_get_all_upcoming_birthdays(mock_session, test_contact):
    """Test getting contacts with upcoming birthdays."""
    mock_contacts = [test_contact]
    
    # Mock the database execute and scalars
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = mock_contacts
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    
    result = await get_all(mock_session, user_id=1, upcoming_birthdays=True)
    
    assert len(result) == 1
    assert result[0].first_name == "Ivan"
    mock_session.execute.assert_called_once()


async def test_get_all_upcoming_birthdays_date_logic(mock_date, mock_session):
    """Test upcoming birthdays date logic."""
    # Mock current date
    mock_date.return_value = date(2024, 1, 1)
    
    # Create contact with birthday in January
    contact_with_birthday = Contact(
        id=2,
        first_name="Maria",
        last_name="Petrenko",
        email="maria@example.com",
        birthday=date(1990, 1, 15),  # Birthday on January 15
        user_id=1,
    )
    
    mock_contacts = [contact_with_birthday]
    
    # Mock the database execute and scalars
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = mock_contacts
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    
    result = await get_all(mock_session, user_id=1, upcoming_birthdays=True)
    
    assert len(result) == 1
    assert result[0].first_name == "Maria"
    assert result[0].birthday.month == 1
    mock_session.execute.assert_called_once()


@pytest.fixture
def mock_date():
    """Mock date fixture for testing date logic."""
    with patch('src.repositories.contact_repository.date') as mock:
        yield mock
