from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, загружаемые из .env."""

    app_name: str = "API Gateway"
    app_version: str = "1.0.0"
    debug: bool = True

    host: str = "0.0.0.0"
    port: int = 8000

    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str

    redis_host: str
    redis_port: int

    cache_ttl: int = 300

    rate_limit: int = 100
    rate_limit_window: int = 60

    circuit_breaker_failures: int = 5
    circuit_breaker_timeout: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    api_keys: str
    # в class Settings добавим:
    service_urls: str = ""
    service_api_keys: str = ""

    @property
    def services_map(self) -> dict[str, str]:
        if not self.service_urls:
            return {
                "weather": "https://httpbin.org/json",
                "news": "https://httpbin.org/json",
                "currency": "https://httpbin.org/json",
            }
        pairs = [s.strip().split(":", 1) for s in self.service_urls.split(",")]
        return {name: url for name, url in pairs if name and url}

    @property
    def service_api_keys_map(self) -> dict[str, tuple[str, str]]:
        """Возвращает словарь {service: (param_name, key)}"""
        if not self.service_api_keys:
            return {}
        result = {}
        for item in self.service_api_keys.split(","):
            parts = item.strip().split(":", 2)
            if len(parts) == 3:
                service, param, key = parts
                result[service] = (param, key)
            elif len(parts) == 2:
                # для обратной совместимости: если только service:key, param="key"
                service, key = parts
                result[service] = ("key", key)
        return result


    @property
    def allowed_api_keys(self) -> set[str]:
        return {
            key.strip()
            for key in self.api_keys.split(",")
            if key.strip()
        }

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"


@lru_cache
def get_settings() -> Settings:
    """Возвращает единственный экземпляр настроек."""
    return Settings()


settings = get_settings()
