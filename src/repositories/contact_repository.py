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
    stmt = select(Contact).where(
        and_(Contact.id == contact_id, Contact.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_email(db: AsyncSession, email: str, user_id: int) -> Optional[Contact]:
    stmt = select(Contact).where(
        and_(Contact.email == email, Contact.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession, contact_data: ContactCreate, user_id: int
) -> Contact:
    db_contact = Contact(**contact_data.model_dump(), user_id=user_id)
    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)
    return db_contact


async def update(
    db: AsyncSession, contact_id: int, contact_data: ContactUpdate, user_id: int
) -> Optional[Contact]:
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
    contact = await get_by_id(db, contact_id, user_id)
    if contact:
        await db.delete(contact)
        await db.commit()
        return True
    return False
