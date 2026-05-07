import pytest
from unittest.mock import patch, AsyncMock
from src.api.health import settings

HEALTH_PATH = "src.api.health"


@pytest.mark.asyncio
async def test_healthcheck_full_success(client):
    """Test: Everything works (200 OK)"""
    with patch(
        f"{HEALTH_PATH}.check_redis_connection", new_callable=AsyncMock
    ) as mock_redis:
        mock_redis.return_value = True

        # Call without prefix, as specified
        response = client.get("/healthcheck")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_healthcheck_database_failure(client):
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.execute", side_effect=Exception("DB Error")
    ):
        response = client.get("/healthcheck")

        assert response.status_code == 503
        assert response.json()["detail"]["database"] == "disconnected"


@pytest.mark.asyncio
async def test_healthcheck_redis_degraded(client):
    """Test: Database OK, but Redis down (degraded)"""
    with patch(
        f"{HEALTH_PATH}.check_redis_connection", new_callable=AsyncMock
    ) as mock_redis:
        mock_redis.return_value = False

        response = client.get("/healthcheck")

        assert response.status_code == 200
        assert response.json()["status"] == "degraded"
        assert response.json()["redis"] == "disconnected"


@pytest.mark.asyncio
async def test_healthcheck_redis_disabled(client):
    # Change ENABLE_REDIS value to False in the settings object itself
    with patch.object(settings, "ENABLE_REDIS", False):
        response = client.get("/healthcheck")

        assert response.status_code == 200
        data = response.json()
        assert data["redis"] == "disabled"
        assert data["status"] == "ok"
