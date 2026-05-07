from __future__ import (
    annotations,
)
from typing import TYPE_CHECKING
from datetime import date

from sqlalchemy import String, Date, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base

if TYPE_CHECKING:
    from src.models.user import User


class Contact(Base):
    """Contact model for storing contact information.
    
    Attributes:
        id: Primary key for the contact.
        user_id: Foreign key referencing the user who owns this contact.
        user: Relationship to the User model.
        first_name: First name of the contact.
        last_name: Last name of the contact.
        email: Email address of the contact.
        phone: Phone number of the contact.
        birthday: Birthday of the contact.
        additional_info: Additional information about the contact.
        __tablename__: Database table name for contacts.
    """
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user: Mapped["User"] = relationship("User", back_populates="contacts")
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), index=True)
    phone: Mapped[str] = mapped_column(String(20))
    birthday: Mapped[date] = mapped_column(Date)
    additional_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # SQLAlchemy table arguments
    __table_args__ = {"extend_existing": True}
    # SQLAlchemy mapper arguments (empty dict for default behavior)
    __mapper_args__ = {}
    
    def __repr__(self) -> str:
        """Return a string representation of the Contact.
        
        Returns:
            str: String representation showing contact name and email.
        """
        return f"<Contact(id={self.id}, name='{self.first_name} {self.last_name}', email='{self.email}')>"
    
    def to_dict(self) -> dict:
        """Convert the Contact instance to a dictionary.
        
        Returns:
            dict: Dictionary containing all contact fields.
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "birthday": self.birthday.isoformat() if self.birthday else None,
            "additional_info": self.additional_info,
        }
    
    @property
    def full_name(self) -> str:
        """Get the full name of the contact.
        
        Returns:
            str: Combined first and last name.
        """
        return " ".join([self.first_name.strip(), self.last_name.strip()]).strip()
    
    def update_from_dict(self, data: dict) -> None:
        """Update contact attributes from a dictionary.
        
        Args:
            data: Dictionary containing fields to update.
                Valid keys are: first_name, last_name, email, phone, 
                birthday, additional_info.
        
        Raises:
            ValueError: If invalid keys are provided in the data dictionary.
        """
        valid_fields = {
            "first_name", "last_name", "email", "phone", 
            "birthday", "additional_info"
        }
        
        invalid_fields = set(data.keys()) - valid_fields
        if invalid_fields:
            raise ValueError(f"Invalid fields: {invalid_fields}")
        
        for key, value in data.items():
            if key == "birthday" and isinstance(value, str):
                from datetime import datetime
                try:
                    setattr(self, key, datetime.strptime(value, "%Y-%m-%d").date())
                except ValueError as e:
                    raise ValueError(f"Invalid date format for birthday: {e}")
            else:
                setattr(self, key, value)
    
    @classmethod
    def create_from_dict(cls, data: dict) -> "Contact":
        """Create a new Contact instance from a dictionary.
        
        Args:
            data: Dictionary containing contact information.
                Required keys: user_id, first_name, last_name, email, phone, birthday.
                Optional keys: additional_info.
        
        Returns:
            Contact: New Contact instance.
        
        Raises:
            ValueError: If required fields are missing or invalid.
        """
        required_fields = {"user_id", "first_name", "last_name", "email", "phone", "birthday"}
        missing_fields = required_fields - set(data.keys())
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        contact = cls()
        contact.user_id = data["user_id"]
        contact.first_name = data["first_name"]
        contact.last_name = data["last_name"]
        contact.email = data["email"]
        contact.phone = data["phone"]
        
        if isinstance(data["birthday"], str):
            from datetime import datetime
            try:
                contact.birthday = datetime.strptime(data["birthday"], "%Y-%m-%d").date()
            except ValueError as e:
                raise ValueError(f"Invalid date format for birthday: {e}")
        else:
            contact.birthday = data["birthday"]
        
        contact.additional_info = data.get("additional_info")
        
        return contact
