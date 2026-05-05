"""
Models module for SQLAlchemy database models.

This module contains all database models used throughout the application
including User, Contact, and their relationships.
"""

from .user import User, UserRole
from .contact import Contact

__all__ = [
    "User",
    "UserRole", 
    "Contact"
]