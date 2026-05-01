import logging
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.redis_client import invalidate_cache
from src.models import User
from src.schemas.user import UserCreate

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        stmt = select(User).filter_by(id=user_id)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        stmt = select(User).filter_by(username=username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).filter_by(email=email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(self, body: UserCreate, avatar: str | None = None) -> User:
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
        user = await self.get_user_by_email(email)
        if user:
            user.confirmed = True
            await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        user = await self.get_user_by_email(email)

        # Перевірка на існування користувача
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
        user = await self.get_user_by_email(email)
        if user:
            user.hashed_password = new_hashed_password
            await self.db.commit()
