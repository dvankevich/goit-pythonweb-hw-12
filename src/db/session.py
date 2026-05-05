from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.config.app_config import settings


engine = create_async_engine(settings.DATABASE_URL, echo=settings.LOG_LEVEL == "DEBUG")

SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """Get database session for FastAPI dependency injection.
    
    Yields:
        AsyncSession: Database session that is automatically closed.
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
