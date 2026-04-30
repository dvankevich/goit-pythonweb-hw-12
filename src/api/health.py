from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.db.session import get_db
from src.db.redis_client import redis_client
from src.config.app_config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])


@router.get("/healthcheck")
async def healthcheck(db: AsyncSession = Depends(get_db)):
    health_status = {"status": "ok", "database": "connected", "redis": "connected"}

    # 1. Перевірка бази даних PostgreSQL
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() != 1:
            raise Exception("Database unexpected result")
    except Exception as e:
        logger.error(f"Database healthcheck failed: {e}")
        health_status["status"] = "error"
        health_status["database"] = "disconnected"

    # 2. Перевірка Redis
    if settings.ENABLE_REDIS:
        try:
            await redis_client.ping()
        except Exception as e:
            logger.error(f"Redis healthcheck failed: {e}")
            health_status["redis"] = "disconnected"
            if health_status["status"] != "error":
                health_status["status"] = "degraded"
    else:
        health_status["redis"] = "disabled"  # Чітко вказуємо, що кеш вимкнено навмисно

    # 3. Прийняття рішення щодо HTTP статусу
    if health_status["database"] == "disconnected":
        # Якщо лежить основна БД — сервіс нежиттєздатний
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status,
        )

    # Якщо БД працює (навіть якщо Redis лежить) — повертаємо 200 OK
    return health_status
