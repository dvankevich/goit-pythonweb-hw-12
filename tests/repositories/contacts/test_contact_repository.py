import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Contact
from src.schemas.contact import ContactCreate, ContactUpdate
from src.repositories.contact_repository import (
    get_all,
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


@pytest.mark.asyncio
async def test_get_all_no_filters(mock_session, test_contact):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [test_contact]
    mock_session.execute = AsyncMock(return_value=mock_result)

    contacts = await get_all(db=mock_session, user_id=1)

    assert len(contacts) == 1
    assert contacts[0].first_name == "Ivan"
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_with_filters(mock_session, test_contact):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [test_contact]
    mock_session.execute = AsyncMock(return_value=mock_result)

    await get_all(db=mock_session, user_id=1, first_name="Ivan")

    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_upcoming_birthdays(mock_session, test_contact):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [test_contact]
    mock_session.execute = AsyncMock(return_value=mock_result)

    await get_all(db=mock_session, user_id=1, upcoming_birthdays=True)

    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_id(mock_session, test_contact):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await get_by_id(db=mock_session, contact_id=1, user_id=1)

    assert result == test_contact
    assert result.id == 1  # type: ignore


@pytest.mark.asyncio
async def test_get_by_email(mock_session, test_contact):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await get_by_email(db=mock_session, email="ivan@example.com", user_id=1)

    assert result == test_contact


@pytest.mark.asyncio
async def test_create_contact(mock_session):
    contact_data = ContactCreate(
        first_name="Petro",
        last_name="Petrov",
        email="petro@example.com",
        phone="123456789",
        birthday=date(1985, 1, 1),
    )

    result = await create(db=mock_session, contact_data=contact_data, user_id=1)

    assert result.first_name == "Petro"
    assert result.user_id == 1
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_contact_success(mock_session, test_contact):
    # Мокаємо пошук контакту перед оновленням
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    update_data = ContactUpdate(first_name="UpdatedName")

    result = await update(
        db=mock_session, contact_id=1, contact_data=update_data, user_id=1
    )

    assert result.first_name == "UpdatedName"  # type: ignore
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(test_contact)


@pytest.mark.asyncio
async def test_update_contact_not_found(mock_session):
    # Контакт не знайдено
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await update(
        db=mock_session, contact_id=99, contact_data=ContactUpdate(), user_id=1
    )

    assert result is None
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_delete_contact_success(mock_session, test_contact):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await delete(db=mock_session, contact_id=1, user_id=1)

    assert result is True
    mock_session.delete.assert_awaited_once_with(test_contact)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_contact_not_found(mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await delete(db=mock_session, contact_id=1, user_id=1)

    assert result is False
    mock_session.delete.assert_not_called()


@pytest.mark.asyncio
@patch("src.repositories.contact_repository.date")  # Перевір шлях до файлу
async def test_get_all_upcoming_birthdays_date_logic(mock_date, mock_session):
    # фіксація дати
    mock_date.today.return_value = date(2025, 12, 29)
    mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    mock_session.execute = AsyncMock(return_value=mock_result)

    await get_all(db=mock_session, user_id=1, upcoming_birthdays=True)

    # отримання SQL рядка
    called_stmt = mock_session.execute.call_args[0][0]
    compiled_sql = str(called_stmt.compile(compile_kwargs={"literal_binds": True}))

    assert "EXTRACT(month FROM contacts.birthday) = 12" in compiled_sql
    assert "EXTRACT(day FROM contacts.birthday) = 29" in compiled_sql
    assert "EXTRACT(month FROM contacts.birthday) = 1" in compiled_sql
    assert "EXTRACT(day FROM contacts.birthday) = 1" in compiled_sql
