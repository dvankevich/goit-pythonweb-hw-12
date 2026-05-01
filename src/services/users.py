import logging
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar
from src.db.redis_client import invalidate_cache
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate):
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            logger.error(f"Error fetching avatar from Gravatar: {e}")

        return await self.repository.create_user(body, avatar)

    async def get_user_by_id(self, user_id: int):
        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str):
        return await self.repository.get_user_by_username(username)

    async def get_user_by_email(self, email: str):
        return await self.repository.get_user_by_email(email)

    async def confirmed_email(self, email: str):
        return await self.repository.confirmed_email(email)

    async def update_avatar_url(self, email: str, url: str):
        return await self.repository.update_avatar_url(email, url)

    async def update_avatar(self, email: str, url: str):
        return await self.repository.update_avatar_url(email, url)
