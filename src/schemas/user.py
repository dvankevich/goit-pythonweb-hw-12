from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from src.models.user import UserRole


class User(BaseModel):
    """Schema for user data.
    
    Attributes:
        id: Unique identifier for the user.
        username: Username of the user.
        email: Email address of the user.
        avatar: URL or path to user's avatar image.
        role: User role (user or admin).
    """
    id: int
    username: str
    email: EmailStr
    avatar: Optional[str] = None
    role: UserRole
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Schema for creating a new user.
    
    Attributes:
        username: Username for the new user (3-50 characters).
        email: Email address for the new user.
        password: Password for the new user (6-100 characters).
    """
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)


class UserResponse(BaseModel):
    """Schema for user response data.
    
    Attributes:
        id: Unique identifier for the user.
        username: Username of the user.
        email: Email address of the user.
        avatar: URL or path to user's avatar image.
        role: User role (user or admin).
        created_at: Timestamp when the user was created.
        confirmed: Whether the user's email has been confirmed.
    """
    id: int
    username: str
    email: EmailStr
    avatar: str | None
    role: UserRole
    created_at: datetime
    confirmed: bool
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for authentication token response.
    
    Attributes:
        access_token: JWT access token for authentication.
        token_type: Type of token (default: "bearer").
    """
    access_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    """Schema for email request operations.
    
    Attributes:
        email: Email address for the request.
    """
    email: EmailStr


class ResetPassword(BaseModel):
    """Schema for password reset requests.
    
    Attributes:
        new_password: New password for the user (6-100 characters).
    """
    new_password: str = Field(min_length=6, max_length=100)
