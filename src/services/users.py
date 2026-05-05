import logging
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar
from src.db.redis_client import invalidate_cache
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related business logic.
    
    Provides high-level user operations including creation,
    retrieval, and profile management.
    
    Attributes:
        repository: The user repository for database operations.
    """
    def __init__(self, db: AsyncSession):
        """Initialize UserService with database session.
        
        Args:
            db: Async database session.
        """
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate):
        """Create a new user with optional Gravatar avatar.
        
        Args:
            body: User creation data.
        
        Returns:
            User: The created user object.
        """
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            logger.error(f"Error fetching avatar from Gravatar: {e}")

        return await self.repository.create_user(body, avatar)

    async def get_user_by_id(self, user_id: int):
        """Retrieve user by ID.
        
        Args:
            user_id: The user ID to search for.
        
        Returns:
            User: The user object if found, None otherwise.
        """
        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str):
        """Retrieve user by username.
        
        Args:
            username: The username to search for.
        
        Returns:
            User: The user object if found, None otherwise.
        """
        return await self.repository.get_user_by_username(username)

    async def get_user_by_email(self, email: str):
        """Retrieve user by email address.
        
        Args:
            email: The email address to search for.
        
        Returns:
            User: The user object if found, None otherwise.
        """
        return await self.repository.get_user_by_email(email)

    async def confirmed_email(self, email: str):
        """Mark user's email as confirmed.
        
        Args:
            email: The email address to confirm.
        
        Returns:
            User: The updated user object.
        """
        return await self.repository.confirmed_email(email)

    async def update_avatar_url(self, email: str, url: str):
        """Update user's avatar URL.
        
        Args:
            email: The user's email address.
            url: The new avatar URL.
        
        Returns:
            User: The updated user object.
        """
        return await self.repository.update_avatar_url(email, url)

    async def update_password(self, email: str, new_password: str):
        """Update user's password.
        
        Args:
            email: The user's email address.
            new_password: The new password to set.
        
        Returns:
            User: The updated user object.
        """
        return await self.repository.update_password(email, new_password)
