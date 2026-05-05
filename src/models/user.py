from __future__ import annotations
from typing import TYPE_CHECKING, List
from datetime import datetime
from enum import Enum
from sqlalchemy import String, func, Enum as SqlEnum  # Додано SqlEnum
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.sql.sqltypes import DateTime

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.contact import Contact


class UserRole(str, Enum):
    """Enumeration for user roles.
    
    Attributes:
        USER: Regular user role.
        ADMIN: Administrator user role.
    """
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """User model for storing user information and authentication data.
    
    Attributes:
        id: Primary key for the user.
        username: Unique username for the user.
        email: Unique email address for the user.
        hashed_password: Hashed password for authentication.
        avatar: URL or path to user's avatar image.
        created_at: Timestamp when the user was created.
        confirmed: Whether the user's email has been confirmed.
        role: User role (user or admin).
        contacts: Relationship to user's contacts.
        __tablename__: Database table name for users.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    confirmed: Mapped[bool] = mapped_column(default=False)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole), default=UserRole.USER, nullable=False
    )
    contacts: Mapped[List["Contact"]] = relationship(
        "Contact", back_populates="user", cascade="all, delete-orphan"
    )
    
    # SQLAlchemy table arguments (empty dict for default behavior)
    __table_args__ = {"extend_existing": True}
    
    # SQLAlchemy mapper arguments (empty dict for default behavior)
    __mapper_args__ = {}
    
    def __repr__(self) -> str:
        """Return a string representation of the User.
        
        Returns:
            str: String representation showing user id, username, and email.
        """
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def to_dict(self) -> dict:
        """Convert the User instance to a dictionary.
        
        Returns:
            dict: Dictionary containing all user fields except password.
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "avatar": self.avatar,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "confirmed": self.confirmed,
            "role": self.role.value,
        }
    
    def is_admin(self) -> bool:
        """Check if the user has admin role.
        
        Returns:
            bool: True if user is admin, False otherwise.
        """
        return self.role == UserRole.ADMIN
    
    def is_confirmed(self) -> bool:
        """Check if the user's email is confirmed.
        
        Returns:
            bool: True if email is confirmed, False otherwise.
        """
        return self.confirmed
    
    def update_from_dict(self, data: dict) -> None:
        """Update user attributes from a dictionary.
        
        Args:
            data: Dictionary containing fields to update.
                Valid keys are: username, email, avatar, confirmed, role.
        
        Raises:
            ValueError: If invalid keys are provided or if username/email already exists.
        """
        valid_fields = {"username", "email", "avatar", "confirmed", "role"}
        
        invalid_fields = set(data.keys()) - valid_fields
        if invalid_fields:
            raise ValueError(f"Invalid fields: {invalid_fields}")
        
        for key, value in data.items():
            if key == "role" and isinstance(value, str):
                try:
                    setattr(self, key, UserRole(value))
                except ValueError as e:
                    raise ValueError(f"Invalid role value: {e}")
            else:
                setattr(self, key, value)
    
    @classmethod
    def create_from_dict(cls, data: dict) -> "User":
        """Create a new User instance from a dictionary.
        
        Args:
            data: Dictionary containing user information.
                Required keys: username, email, hashed_password.
                Optional keys: avatar, confirmed, role.
        
        Returns:
            User: New User instance.
        
        Raises:
            ValueError: If required fields are missing or invalid.
        """
        required_fields = {"username", "email", "hashed_password"}
        missing_fields = required_fields - set(data.keys())
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        user = cls()
        user.username = data["username"]
        user.email = data["email"]
        user.hashed_password = data["hashed_password"]
        user.avatar = data.get("avatar")
        user.confirmed = data.get("confirmed", False)
        
        role_value = data.get("role", "user")
        if isinstance(role_value, str):
            try:
                user.role = UserRole(role_value)
            except ValueError as e:
                raise ValueError(f"Invalid role value: {e}")
        else:
            user.role = role_value
        
        return user
