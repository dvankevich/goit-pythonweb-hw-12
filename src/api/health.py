from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.db.session import get_db
from src.db.redis_client import redis_client, check_redis_connection
from src.config.app_config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])


@router.get("/healthcheck")
async def healthcheck(db: AsyncSession = Depends(get_db)):
    """Check system health including database and Redis connectivity.
    
    Args:
        db: Async database session.
    
    Returns:
        dict: Health status information.
    
    Raises:
        HTTPException: If database is disconnected.
    """
    health_status = {"status": "ok", "database": "connected", "redis": "connected"}

    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database healthcheck failed: {e}")
        health_status.update({"status": "error", "database": "disconnected"})

    if settings.ENABLE_REDIS:
        is_redis_up = await check_redis_connection()
        if not is_redis_up:
            health_status["redis"] = "disconnected"
            if health_status["status"] != "error":
                health_status["status"] = "degraded"
    else:
        health_status["redis"] = "disabled"

    if health_status["database"] == "disconnected":
        raise HTTPException(status_code=503, detail=health_status)

    return health_status
