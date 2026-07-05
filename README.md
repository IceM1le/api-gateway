# ⚡ API Gateway

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7+-DC382D.svg)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-✓-2496ED.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-pytest-brightgreen.svg)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## О проекте

**API Gateway** — асинхронный шлюз на **FastAPI**, единая точка входа для клиентских запросов к внешним сервисам (погода, новости, валюта).
Реализованы промышленные паттерны для защиты, оптимизации и наблюдаемости:

- **Аутентификация** по API-ключам (хранятся в PostgreSQL, хеширование SHA‑256)
- **Rate Limiting** (скользящее окно в Redis, раздельно по сервисам)
- **Кэширование** ответов в Redis с настраиваемым TTL
- **Circuit Breaker** с состояниями CLOSED/OPEN/HALF_OPEN (персистентный в Redis, на каждый сервис)
- **Логирование** каждого запроса в PostgreSQL (асинхронно, не замедляет ответ)
- **Трассировка** запросов (OpenTelemetry → Jaeger)
- **Метрики** для Prometheus
- **Контейнеризация** через Docker Compose
- **Тесты** (pytest, моки, 100% покрытие критических сценариев)

Идеальный проект для демонстрации навыков backend‑разработки и архитектурного мышления.

---

## Стек технологий

| Компонент            | Технология                                         |
|----------------------|----------------------------------------------------|
| Язык                 | Python 3.12+                                       |
| Фреймворк            | FastAPI (асинхронный)                              |
| База данных          | PostgreSQL 16 + async SQLAlchemy + Alembic         |
| Кэш                  | Redis 7                                            |
| HTTP‑клиент          | aiohttp                                            |
| Аутентификация       | Хеширование SHA‑256, хранение ключей в БД         |
| Rate Limiting        | Sliding window (сортированные множества Redis)     |
| Circuit Breaker      | Собственная реализация, состояние хранится в Redis |
| Телеметрия           | OpenTelemetry SDK + Jaeger + Prometheus            |
| Тестирование         | pytest, pytest‑asyncio, respx (моки HTTP), моки Redis |
| Контейнеризация      | Docker, Docker Compose                             |

---

## Архитектура проекта

```text
.
├── app
│   ├── api
│   │   ├── dependencies.py          # Depends (get_api_key, get_http_client)
│   │   ├── middleware
│   │   │   ├── logging.py           # Логирование + Prometheus метрики
│   │   │   ├── metrics.py           # (удалён – используется LoggingMiddleware)
│   │   │   ├── rate_limit.py        # Проверка лимита через RateLimiter
│   │   │   └── tracing.py           # (удалён – ОTel инструментирование)
│   │   ├── routers
│   │   │   ├── gateway.py           # Динамический роутер /api/{service}/{path}
│   │   │   ├── health.py
│   │   │   └── metrics.py
│   │   └── router.py
│   ├── core
│   │   ├── circuit_breaker.py       # (старая версия, не используется)
│   │   ├── config.py                # Pydantic‑Settings
│   │   ├── dependencies.py          # Инициализация rate_limiter, redis
│   │   ├── logger.py
│   │   ├── metrics.py               # Prometheus счётчики/гистограммы
│   │   ├── rate_limiter.py          # Sliding window Redis rate limiter
│   │   ├── security.py              # (устаревшая проверка ключей из .env)
│   │   └── tracing.py               # Настройка ОTel
│   ├── db
│   │   ├── dependencies.py          # AsyncSessionLocal
│   │   ├── models.py                # RequestLog, ApiKey
│   │   └── redis.py
│   ├── services
│   │   ├── api_key_service.py       # Сервис проверки и хеширования ключей
│   │   ├── base_service.py
│   │   ├── cache_service.py         # → заменён на redis_cache.py
│   │   ├── circuit_breaker_registry.py  # CircuitBreakerRegistry + CircuitBreaker (Redis)
│   │   ├── dashboard_service.py
│   │   ├── health_service.py
│   │   ├── http_client.py           # HttpClient (кэш + CB)
│   │   ├── redis_cache.py           # Низкоуровневый кэш‑сервис
│   │   ├── request_log_service.py   # Запись логов в БД
│   │   └── weather_service.py       # (пример, удалён)
│   └── utils
├── docker
├── migrations
│   ├── versions
│   └── env.py
├── tests
│   └── test_gateway.py
├── docker-compose.yml
├── docker-compose.override.yml
├── Dockerfile
├── .env.example
└── requirements.txt
```

### Поток обработки одного запроса

1. **Клиент** → `GET /api/{service}/{path}` + заголовок `X-API-Key`
2. **Rate Limiting** (Redis) — превышен лимит → `429 Too Many Requests`
3. **Аутентификация** (PostgreSQL) — ключ не валиден → `401 Unauthorized`
4. **Проверка кэша** (Redis) — найдено → мгновенный ответ
5. **Circuit Breaker** проверяет состояние сервиса
6. **Запрос к внешнему API** (aiohttp)
   - Успех → сохранить в кэш, вернуть данные
   - Ошибка → обновить счётчик ошибок, возможно открыть CB, вернуть `503` или fallback
7. **Логирование** в PostgreSQL (фоновая задача, ответ клиенту уже ушёл)
8. **Трассировка** и **метрики** фиксируются на каждом шагу

---

## Быстрый старт

### 1. Клонировать репозиторий
```bash
git clone https://github.com/yourname/your-api-gateway.git
cd your-api-gateway
```

### 2. Создать файл .env на основе примера
```bash
cp .env.example .env
```
Заполните `.env` своими ключами внешних API и параметрами (см. секцию **Конфигурация** ниже).

### 3. Запустить через Docker Compose
```bash
docker compose up -d --build
```

### 4. Применить миграции 
```bash
docker compose exec api alembic upgrade head
```

### 5. Добавить тестовый API‑ключ в БД
```bash
docker compose exec api python -c "
import asyncio, hashlib
from app.db.dependencies import AsyncSessionLocal
from app.db.models import ApiKey

raw_key = 'test-key-1'
key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

async def add():
    async with AsyncSessionLocal() as db:
        db.add(ApiKey(key_hash=key_hash, client_name='Test Client', rate_limit=100, is_active=True))
        await db.commit()
        print('Key added:', key_hash)

asyncio.run(add())
"
```

### 6. Открыть Swagger UI
Перейдите по адресу [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Примеры запросов

### Погода (с кэшированием)
```bash
curl -X GET "http://localhost:8000/api/weather/current.json?q=London" \
     -H "X-API-Key: test-key-1"
```

### Новости (параметр apiKey добавляется автоматически)
```bash
curl -X GET "http://localhost:8000/api/news/top-headlines?country=us" \
     -H "X-API-Key: test-key-1"
```

### Курсы валют
```bash
curl -X GET "http://localhost:8000/api/currency/USD" \
     -H "X-API-Key: test-key-1"
```

### Health check
```bash
curl -X GET "http://localhost:8000/health"
```

---

## Конфигурация (.env)

```ini
APP_NAME=API Gateway
APP_VERSION=1.0.0
DEBUG=True
HOST=0.0.0.0
PORT=8000

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=gateway
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

REDIS_HOST=redis
REDIS_PORT=6379

CACHE_TTL=300
RATE_LIMIT=100
RATE_LIMIT_WINDOW=60

CIRCUIT_BREAKER_FAILURES=5
CIRCUIT_BREAKER_TIMEOUT=30

SERVICE_URLS=weather:https://api.weatherapi.com/v1,news:https://newsapi.org/v2,currency:https://api.exchangerate-api.com/v4/latest
SERVICE_API_KEYS=weather:key:YOUR_WEATHER_API_KEY,news:apiKey:YOUR_NEWS_API_KEY,currency::
```

Формат `SERVICE_API_KEYS`: `service:query_param_name:api_key`.
Если API не требует ключа, оставьте параметр пустым (например, `currency::`).

---

##  Тестирование

Все тесты изолированы (моки Redis и внешних HTTP‑запросов) и запускаются в контейнере:
```bash
docker compose exec api sh -c "PYTHONPATH=/app pytest tests/"
```
