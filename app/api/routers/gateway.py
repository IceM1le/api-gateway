from fastapi import APIRouter, Depends, Request, HTTPException
from app.api.dependencies import get_api_key
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
    api_key: str = Depends(get_api_key),
):
    # Ищем внешний URL сервиса
    base_url = settings.services_map.get(service.lower())
    if not base_url:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service}'")

    target_url = f"{base_url}/{path}" if path else base_url

    # Собираем query-параметры из исходного запроса
    params = dict(request.query_params)

    # Добавляем API-ключ сервиса, если он задан
    service_key_entry = settings.service_api_keys_map.get(service.lower())
    if service_key_entry:
        param_name, api_key_value = service_key_entry
        if param_name:  # если param_name не пустой
            params[param_name] = api_key_value

    # Проксируем GET-запрос
    data = await client.get(service.lower(), target_url, params=params)
    return data