import logging
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.redis_client import invalidate_cache
from src.models import User
from src.schemas.user import UserCreate

logger = logging.getLogger(__name__)


class UserRepository:
    """
    Repository class for managing User-related database operations.

    Attributes:
        db (AsyncSession): The asynchronous database session.
    """

    def __init__(self, session: AsyncSession):
        """
        Initializes the UserRepository with a database session.

        Args:
            session (AsyncSession): The SQLAlchemy async session.
        """
        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieve a user from the database by their unique ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User | None: The User object if found, otherwise None.
        """
        stmt = select(User).filter_by(id=user_id)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Retrieve a user from the database by their username.

        Args:
            username (str): The username to search for.

        Returns:
            User | None: The User object if found, otherwise None.
        """
        stmt = select(User).filter_by(username=username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user from the database by their email address.

        Args:
            email (str): The email address to search for.

        Returns:
            User | None: The User object if found, otherwise None.
        """
        stmt = select(User).filter_by(email=email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(self, body: UserCreate, avatar: str | None = None) -> User:
        """
        Create a new user in the database.

        Args:
            body (UserCreate): The schema containing user data (username, email, password).
            avatar (str | None, optional): The URL to the user's avatar image. Defaults to None.

        Returns:
            User: The newly created User object.
        """
        user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=body.password,
            avatar=avatar,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def confirmed_email(self, email: str) -> None:
        """
        Mark a user's email as confirmed in the database.

        Args:
            email (str): The email address of the user to confirm.
        """
        user = await self.get_user_by_email(email)
        if user:
            user.confirmed = True
            await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        """
        Update the avatar URL for a specific user and invalidate their cache.

        Args:
            email (str): The email of the user whose avatar is being updated.
            url (str): The new avatar URL.

        Raises:
            HTTPException: If the user with the specified email does not exist.

        Returns:
            User: The updated User object.
        """
        user = await self.get_user_by_email(email)

        if user is None:
            logger.error(f"Attempted to update avatar for non-existent user: {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)

        await invalidate_cache(f"user:{user.username}")
        return user

    async def update_password(self, email: str, new_hashed_password: str) -> None:
        """
        Update a user's password with a new hashed password.

        Args:
            email (str): The email address of the user.
            new_hashed_password (str): The pre-hashed new password.
        """
        user = await self.get_user_by_email(email)
        if user:
            user.hashed_password = new_hashed_password
            await self.db.commit()
