from datetime import date
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional


class ContactBase(BaseModel):
    """Base schema for contact data.
    
    Attributes:
        first_name: First name of the contact.
        last_name: Last name of the contact.
        email: Email address of the contact.
        phone: Phone number of the contact.
        birthday: Birthday of the contact.
        additional_info: Additional information about the contact.
    """
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: date
    additional_info: str | None = None


class ContactCreate(ContactBase):
    """Schema for creating a new contact.
    
    Inherits all fields from ContactBase for contact creation.
    """
    pass


class ContactResponse(ContactBase):
    """Schema for contact response data.
    
    Inherits all fields from ContactBase and adds the contact ID.
    
    Attributes:
        id: Unique identifier for the contact.
    """
    id: int
    model_config = ConfigDict(from_attributes=True)


class ContactUpdate(BaseModel):
    """Schema for updating an existing contact.
    
    All fields are optional to allow partial updates.
    
    Attributes:
        first_name: Updated first name of the contact.
        last_name: Updated last name of the contact.
        email: Updated email address of the contact.
        phone: Updated phone number of the contact.
        birthday: Updated birthday of the contact.
        additional_info: Updated additional information about the contact.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birthday: Optional[date] = None
    additional_info: Optional[str] = None
