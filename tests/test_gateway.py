import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
import respx
import httpx

from app.main import app
from app.api.dependencies import get_api_key
from app.api.routers.gateway import get_http_client
from app.services.http_client import HttpClient

# ==========================
# Константы
# ==========================
VALID_TEST_KEY = "test-key-1"


# ==========================
# Мок проверки API-ключа
# ==========================
async def mock_get_api_key(x_api_key: str = VALID_TEST_KEY):
    from fastapi import HTTPException, status
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    if x_api_key != VALID_TEST_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return x_api_key


app.dependency_overrides[get_api_key] = mock_get_api_key


# ==========================
# Мок HttpClient – переопределяем через dependency_overrides
# ==========================
@pytest.fixture
def mock_http_client():
    """Создаёт HttpClient с мокнутым Redis."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.incr = AsyncMock(return_value=1)
    from app.services.redis_cache import RedisCache
    from app.services.circuit_breaker_registry import CircuitBreakerRegistry
    cache = RedisCache(mock_redis)
    cb_registry = CircuitBreakerRegistry(mock_redis)
    return HttpClient(cb_registry, cache)


@pytest.fixture(autouse=True)
def mock_service_keys():
    """Во всех тестах подменяем service_api_keys_map на тестовые ключи."""
    from unittest.mock import patch
    from app.core.config import settings
    test_keys = {
        'weather': ('key', 'c6610f0da37340ae828160047260407'),
        'currency': ('', ''),
    }
    with patch.object(settings, 'service_api_keys_map', test_keys):
        yield


@pytest_asyncio.fixture
async def client(mock_http_client):
    """Тестовый клиент с подменённым HttpClient."""
    # Подменяем зависимость get_http_client на возврат нашего мока
    app.dependency_overrides[get_http_client] = lambda: mock_http_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    # Убираем переопределение после теста
    app.dependency_overrides.pop(get_http_client, None)


# ==========================
# Мок RateLimiter – чтобы не лезть в Redis
# ==========================
@pytest.fixture(autouse=True)
def mock_rate_limiter():
    from app.core.dependencies import rate_limiter
    with patch.object(rate_limiter, 'is_allowed', return_value=True):
        yield


# ==========================
# Тесты
# ==========================
@pytest.mark.asyncio
@respx.mock
async def test_weather_proxy_success(client, mock_http_client):
    mock_resp = {"location": {"name": "Moscow"}, "current": {"temp_c": 20}}
    respx.get("https://api.weatherapi.com/v1/current.json?q=Moscow&key=c6610f0da37340ae828160047260407").mock(
        return_value=httpx.Response(200, json=mock_resp)
    )
    response = await client.get("/api/weather/current.json?q=Moscow", headers={"X-API-Key": VALID_TEST_KEY})
    assert response.status_code == 200
    assert response.json()["location"]["name"] == "Moscow"


@pytest.mark.asyncio
@respx.mock
async def test_currency_proxy_success(client, mock_http_client):
    mock_resp = {"base": "USD", "rates": {"EUR": 0.85}}
    respx.get("https://api.exchangerate-api.com/v4/latest/USD").mock(
        return_value=httpx.Response(200, json=mock_resp)
    )
    response = await client.get("/api/currency/USD", headers={"X-API-Key": VALID_TEST_KEY})
    assert response.status_code == 200
    assert response.json()["base"] == "USD"


@pytest.mark.asyncio
async def test_missing_api_key(client):
    response = await client.get("/api/weather/current.json?q=Moscow")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing API key"


@pytest.mark.asyncio
async def test_invalid_api_key(client):
    response = await client.get("/api/weather/current.json?q=Moscow", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"


@pytest.mark.asyncio
@respx.mock
async def test_unknown_service(client, mock_http_client):
    response = await client.get("/api/unknown_service/some/path", headers={"X-API-Key": VALID_TEST_KEY})
    assert response.status_code == 404
    assert "Unknown service" in response.json()["detail"]
