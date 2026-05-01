import logging
import asyncio
import redis.asyncio as redis
from typing import cast, Awaitable
from src.config.app_config import settings

logger = logging.getLogger(__name__)

# Створюємо пул з'єднань окремо. Це надійніший спосіб передачі таймаутів
# в асинхронному середовищі, оскільки пул керує кожним новим сокетом.
pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True,
    socket_timeout=0.1,  # 100мс на відповідь від Redis
    socket_connect_timeout=0.1,  # 100мс на встановлення TCP-з'єднання
    max_connections=20,  # Обмеження пулу для запобігання витоку ресурсів
    retry_on_timeout=False,  # Відразу йдемо в fallback (БД) при таймауті
)

# Ініціалізуємо клієнт через пул
redis_client = redis.Redis(connection_pool=pool)


async def check_redis_connection() -> bool:
    """
    Перевірка з'єднання з жорстким зовнішнім таймаутом.
    Навіть якщо DNS або TCP затримаються, asyncio.wait_for перерве виконання.
    """
    if not settings.ENABLE_REDIS:
        return False

    try:
        # Зовнішній таймаут 200мс для гарантії швидкодії
        return await asyncio.wait_for(cast(Awaitable[bool], redis_client.ping()), timeout=0.2)
    except asyncio.TimeoutError:
        logger.warning("Redis connection timed out (external limit).")
        return False
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False


async def get_redis():
    """Повертає клієнт Redis (для FastAPI Dependency Injection)"""
    return redis_client


async def invalidate_cache(key: str):
    """Видаляє запис із кешу при оновленні даних"""
    if settings.ENABLE_REDIS:
        try:
            # Додаємо логування перед видаленням
            logger.debug(f"Attempting to invalidate Redis cache for key: {key}")

            result = await redis_client.delete(key)

            if result:
                logger.debug(f"Successfully invalidated cache for key: {key}")
            else:
                logger.debug(f"Cache key not found, nothing to delete: {key}")

        except Exception as e:
            logger.error(f"Failed to invalidate cache for {key}: {e}")
