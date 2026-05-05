from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.
    
    Inherits from SQLAlchemy's DeclarativeBase to provide
    common functionality for all database models.
    
    Attributes:
        metadata: SQLAlchemy metadata container for all models.
    """
