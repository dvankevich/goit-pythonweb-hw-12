import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.models.user import User, UserRole
from src.config.app_config import settings
from src.services.auth import Hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_admin():
    async for db in get_db():
        query = select(User).filter(
            (User.email == settings.ADMIN_EMAIL)
            | (User.username == settings.ADMIN_USERNAME)
        )
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.info(f"Admin user already exists: {existing_user.username}")
            return

        hashed_password = Hash().get_password_hash(
            settings.ADMIN_PASSWORD.get_secret_value()
        )

        new_admin = User(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            confirmed=True,
            avatar=None,
        )

        try:
            db.add(new_admin)
            await db.commit()
            await db.refresh(new_admin)
            logger.info(f"Successfully created admin: {new_admin.username}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create admin: {e}")


if __name__ == "__main__":
    asyncio.run(create_admin())
