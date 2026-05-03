import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.contact_repository import (
    get_all,
    get_by_id,
    get_by_email,
    create,
    update,
    delete,
)
from src.schemas.contact import ContactCreate, ContactUpdate
from src.models import Contact


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def contact_data():
    return ContactCreate(
        first_name="Dima",
        last_name="Dev",
        email="dima@example.com",
        phone="+380000000000",
        birthday=date(1995, 1, 1),
    )


@pytest.mark.asyncio
async def test_get_all_contacts(mock_session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [Contact(id=1, user_id=1)]
    mock_session.execute.return_value = mock_result

    contacts = await get_all(mock_session, user_id=1)

    assert len(contacts) == 1
    assert contacts[0].id == 1
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_upcoming_birthdays(mock_session):
    # імітація результату БД
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    # виклик функції з upcoming_birthdays=True
    await get_all(mock_session, user_id=1, upcoming_birthdays=True)

    # об'єкт запиту  який переданов  execute
    args, _ = mock_session.execute.call_args
    query_str = str(args[0]).lower()

    # перевірка запиту на наявність потрібних атрибутів і функцій
    assert "extract" in query_str
    assert "or" in query_str
    assert "user_id" in query_str


@pytest.mark.asyncio
async def test_create_contact(mock_session, contact_data):
    result = await create(mock_session, contact_data, user_id=1)

    assert result.first_name == "Dima"
    assert result.user_id == 1
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_contact_success(mock_session):
    # Імітуємо існуючий контакт
    existing_contact = Contact(id=1, first_name="Old", user_id=1)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute.return_value = mock_result

    update_data = ContactUpdate(first_name="New Name")
    result = await update(mock_session, 1, update_data, 1)

    assert result.first_name == "New Name"  # type: ignore
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_contact_not_found(mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await update(mock_session, 1, ContactUpdate(), 1)
    assert result is None


@pytest.mark.asyncio
async def test_delete_contact_found(mock_session):
    contact = Contact(id=1, user_id=1)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = contact
    mock_session.execute.return_value = mock_result

    result = await delete(mock_session, 1, 1)

    assert result is True
    mock_session.delete.assert_called_with(contact)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_contact_not_found(mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await delete(mock_session, 1, 1)
    assert result is False
