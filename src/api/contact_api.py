from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from src.schemas.contact import ContactCreate, ContactResponse, ContactUpdate
from src.repositories import contact_repository
from src.models.user import User
from src.services.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # Отримуємо поточного користувача
):
    """Create a new contact for the authenticated user.
    
    Args:
        contact: Contact data to create.
        db: Async database session.
        current_user: Authenticated user instance.
    
    Returns:
        ContactResponse: The newly created contact.
    
    Raises:
        HTTPException: If contact with same email already exists.
    """
    existing_contact = await contact_repository.get_by_email(
        db, email=contact.email, user_id=current_user.id
    )

    if existing_contact:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Contact with email '{contact.email}' already exists in your list.",
        )

    return await contact_repository.create(db, contact, user_id=current_user.id)


@router.get("/", response_model=List[ContactResponse])
async def read_contacts(
    first_name: Optional[str] = Query(None, description="find by first name"),
    last_name: Optional[str] = Query(None, description="find by second name"),
    email: Optional[str] = Query(None, description="find by email"),
    upcoming_birthdays: bool = Query(
        False, description="Show only contacts with birthdays in the next 7 days"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all contacts for the authenticated user with optional filtering.
    
    Args:
        first_name: Filter contacts by first name.
        last_name: Filter contacts by last name.
        email: Filter contacts by email.
        upcoming_birthdays: Filter contacts with birthdays in next 7 days.
        db: Async database session.
        current_user: Authenticated user instance.
    
    Returns:
        List[ContactResponse]: List of contacts matching the criteria.
    """
    contacts = await contact_repository.get_all(
        db,
        user_id=current_user.id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        upcoming_birthdays=upcoming_birthdays,
    )
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def read_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific contact by ID.
    
    Args:
        contact_id: ID of the contact to retrieve.
        db: Async database session.
        current_user: Authenticated user instance.
    
    Returns:
        ContactResponse: The requested contact.
    
    Raises:
        HTTPException: If contact not found or access denied.
    """
    contact = await contact_repository.get_by_id(
        db, contact_id, user_id=current_user.id
    )
    if not contact:
        raise HTTPException(
            status_code=404, detail="Contact not found or access denied"
        )
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    body: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a specific contact.
    
    Args:
        contact_id: ID of the contact to update.
        body: Updated contact data.
        db: Async database session.
        current_user: Authenticated user instance.
    
    Returns:
        ContactResponse: The updated contact.
    
    Raises:
        HTTPException: If contact not found, access denied, or email conflict.
    """
    if body.email:
        existing_contact = await contact_repository.get_by_email(
            db, email=body.email, user_id=current_user.id
        )

        if existing_contact and existing_contact.id != contact_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{body.email}' is already taken by another of your contacts.",
            )

    updated_contact = await contact_repository.update(
        db, contact_id, body, user_id=current_user.id
    )

    if updated_contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact not found or access denied",
        )

    return updated_contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a specific contact.
    
    Args:
        contact_id: ID of the contact to delete.
        db: Async database session.
        current_user: Authenticated user instance.
    
    Returns:
        None: Success response with no content.
    
    Raises:
        HTTPException: If contact not found or access denied.
    """
    success = await contact_repository.delete(db, contact_id, user_id=current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact not found or access denied",
        )

    return None
