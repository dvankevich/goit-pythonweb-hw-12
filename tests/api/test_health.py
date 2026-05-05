import pytest
from unittest.mock import patch, AsyncMock
from src.api.health import settings

HEALTH_PATH = "src.api.health"


@pytest.mark.asyncio
async def test_healthcheck_full_success(client):
    """Тест: Все працює (200 OK)"""
    with patch(
        f"{HEALTH_PATH}.check_redis_connection", new_callable=AsyncMock
    ) as mock_redis:
        mock_redis.return_value = True

        # Виклик без префікса, як ви вказали
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
    """Тест: База ок, але Redis впав (degraded)"""
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
    # Підміняємо значення ENABLE_REDIS на False в самому об'єкті settings
    with patch.object(settings, "ENABLE_REDIS", False):
        response = client.get("/healthcheck")

        assert response.status_code == 200
        data = response.json()
        assert data["redis"] == "disabled"
        assert data["status"] == "ok"
