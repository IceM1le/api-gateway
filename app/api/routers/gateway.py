from fastapi import APIRouter, Depends, Request, HTTPException
from app.api.dependencies import require_api_key
from app.core.config import settings
from app.services.http_client import HttpClient

router = APIRouter(prefix="/api", tags=["Gateway"])


async def get_http_client(request: Request) -> HttpClient:
    return request.app.state.http_client


@router.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(
    service: str,
    path: str,
    request: Request,
    client: HttpClient = Depends(get_http_client),
    api_key: str = Depends(require_api_key),
):
    # Ищем внешний URL сервиса
    base_url = settings.services_map.get(service.lower())
    if not base_url:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service}'")

    target_url = f"{base_url}/{path}" if path else base_url

    # Собираем query-параметры из исходного запроса
    params = dict(request.query_params)

    # Добавляем API-ключ сервиса, если он задан
    service_api_key = settings.service_api_keys_map.get(service.lower())
    if service_api_key:
        # WeatherAPI ожидает параметр 'key'
        params["key"] = service_api_key

    # Проксируем GET-запрос
    data = await client.get(target_url, params=params)
    return data