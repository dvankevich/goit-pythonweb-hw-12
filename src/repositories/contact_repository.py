from typing import Optional, List
from datetime import date, timedelta
from sqlalchemy import select, and_, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Contact
from src.schemas.contact import ContactCreate, ContactUpdate


async def get_all(
    db: AsyncSession,
    user_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    upcoming_birthdays: bool = False,
) -> List[Contact]:
    """
    Retrieve a list of contacts for a specific user with optional filters.

    Args:
        db (AsyncSession): The database session.
        user_id (int): The ID of the user owning the contacts.
        first_name (str | None, optional): Filter by first name (case-insensitive partial match).
        last_name (str | None, optional): Filter by last name (case-insensitive partial match).
        email (str | None, optional): Filter by email address (case-insensitive partial match).
        upcoming_birthdays (bool, optional): If True, filters contacts having birthdays within the next 7 days.

    Returns:
        List[Contact]: A list of contact objects matching the criteria.
    """

    stmt = select(Contact).where(Contact.user_id == user_id)

    if first_name:
        stmt = stmt.where(Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        stmt = stmt.where(Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        stmt = stmt.where(Contact.email.ilike(f"%{email}%"))

    if upcoming_birthdays:
        today = date.today()
        upcoming_conditions = []

        for i in range(7):
            future_date = today + timedelta(days=i)
            upcoming_conditions.append(
                and_(
                    extract("month", Contact.birthday) == future_date.month,
                    extract("day", Contact.birthday) == future_date.day,
                )
            )

        stmt = stmt.where(or_(*upcoming_conditions))

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_by_id(
    db: AsyncSession, contact_id: int, user_id: int
) -> Optional[Contact]:
    """
    Retrieve a single contact by its unique identifier and owner ID.

    Args:
        db (AsyncSession): The database session.
        contact_id (int): The unique ID of the contact.
        user_id (int): The ID of the user owning the contact.

    Returns:
        Optional[Contact]: The contact object if found, otherwise None.
    """
    stmt = select(Contact).where(
        and_(Contact.id == contact_id, Contact.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_email(db: AsyncSession, email: str, user_id: int) -> Optional[Contact]:
    """
    Retrieve a single contact by its email address.

    Args:
        db (AsyncSession): The database session.
        email (str): The email address to search for.
        user_id (int): The ID of the user owning the contact.

    Returns:
        Optional[Contact]: The contact object if found, otherwise None.
    """
    stmt = select(Contact).where(
        and_(Contact.email == email, Contact.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession, contact_data: ContactCreate, user_id: int
) -> Contact:
    """
    Create a new contact in the database.

    Args:
        db (AsyncSession): The database session.
        contact_data (ContactCreate): The data for the new contact.
        user_id (int): The ID of the user creating the contact.

    Returns:
        Contact: The newly created contact object.
    """
    db_contact = Contact(**contact_data.model_dump(), user_id=user_id)
    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)
    return db_contact


async def update(
    db: AsyncSession, contact_id: int, contact_data: ContactUpdate, user_id: int
) -> Optional[Contact]:
    """
    Update an existing contact's information.

    Args:
        db (AsyncSession): The database session.
        contact_id (int): The ID of the contact to update.
        contact_data (ContactUpdate): The new data for the contact.
        user_id (int): The ID of the user owning the contact.

    Returns:
        Optional[Contact]: The updated contact object if successful, otherwise None.
    """
    db_contact = await get_by_id(db, contact_id, user_id)
    if not db_contact:
        return None

    update_data = contact_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_contact, key, value)

    await db.commit()
    await db.refresh(db_contact)
    return db_contact


async def delete(db: AsyncSession, contact_id: int, user_id: int) -> bool:
    """
    Remove a contact from the database.

    Args:
        db (AsyncSession): The database session.
        contact_id (int): The ID of the contact to delete.
        user_id (int): The ID of the user owning the contact.

    Returns:
        bool: True if the contact was successfully deleted, False otherwise.
    """
    contact = await get_by_id(db, contact_id, user_id)
    if contact:
        await db.delete(contact)
        await db.commit()
        return True
    return False
