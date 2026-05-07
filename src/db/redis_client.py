import logging
import asyncio
import redis.asyncio as redis
from typing import cast, Awaitable
from src.config.app_config import settings

logger = logging.getLogger(__name__)

# Create connection pool separately. This is a more reliable way to pass timeouts
# in async environment, as pool manages each new socket.
pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True,
    socket_timeout=0.1,  # 100ms for response from Redis
    socket_connect_timeout=0.1,  # 100ms for TCP connection establishment
    max_connections=20,  # Pool limit to prevent resource leaks
    retry_on_timeout=False,  # Immediately go to fallback (DB) on timeout
)

# Initialize client through pool
redis_client = redis.Redis(connection_pool=pool)


async def check_redis_connection() -> bool:
    """Check Redis connection with hard external timeout.
    
    Even if DNS or TCP are delayed, asyncio.wait_for will
    interrupt execution to prevent hanging.
    
    Returns:
        bool: True if Redis connection is successful, False otherwise.
    """
    if not settings.ENABLE_REDIS:
        return False

    try:
        # External timeout 200ms to guarantee responsiveness
        return await asyncio.wait_for(cast(Awaitable[bool], redis_client.ping()), timeout=0.2)
    except asyncio.TimeoutError:
        logger.warning("Redis connection timed out (external limit).")
        return False
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False


async def get_redis():
    """Return Redis client for FastAPI Dependency Injection.
    
    Returns:
        Redis: The Redis client instance.
    """
    return redis_client


async def invalidate_cache(key: str):
    """Delete record from cache when data is updated.
    
    Args:
        key: The cache key to invalidate.
    """
    if settings.ENABLE_REDIS:
        try:
            # Add logging before deletion
            logger.debug(f"Attempting to invalidate Redis cache for key: {key}")

            result = await redis_client.delete(key)

            if result:
                logger.debug(f"Successfully invalidated cache for key: {key}")
            else:
                logger.debug(f"Cache key not found, nothing to delete: {key}")

        except Exception as e:
            logger.error(f"Failed to invalidate cache for {key}: {e}")
