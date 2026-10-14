# Deribit Price Tracker

Сервис собирает индексные цены `btc_usd` и `eth_usd` с Deribit раз в минуту, сохраняет историю в PostgreSQL и предоставляет HTTP API на FastAPI. Сбор выполняют Celery worker и Celery Beat; Redis используется как брокер задач.

## Возможности

- Получение актуальной индексной цены через публичный Deribit API, без API-ключа.
- Периодический сбор BTC и ETH раз в минуту с сохранением UNIX timestamp в секундах.
- REST API для полной истории, последней цены и истории за конкретный UTC-день.
- Версионирование схемы базы данных с Alembic.
- Docker Compose для PostgreSQL, Redis, миграций, API, Celery worker и Celery Beat.
- Unit/API тесты с SQLite в памяти и GitHub Actions для pytest и Ruff на push и pull request.

## Архитектура

```text
Deribit public API
        │ aiohttp
        ▼
Celery Beat ──► Redis ──► Celery worker ──► PriceRepository ──► PostgreSQL
                                                            ▲
FastAPI routes ──► PriceService ──► PriceRepository ────────┘
```

`app/clients.py` изолирует внешний API, `app/worker.py` отвечает за запуск сбора, `app/services.py` содержит бизнес-правила, а `app/repositories.py` — операции хранения. HTTP-слой не содержит запросов к Deribit и работает с базой через сервис и репозиторий. Миграция таблицы хранится в `migrations/versions`.

## API

Все методы — `GET`, параметр `ticker` обязателен. Допустимые значения: `btc_usd`, `eth_usd` (регистр не важен). Документация OpenAPI доступна по `/docs`.

| Метод | Назначение |
| --- | --- |
| `GET /prices?ticker=btc_usd` | Все сохранённые цены тикера, от новых к старым |
| `GET /prices/latest?ticker=btc_usd` | Последняя сохранённая цена; `404`, если данных ещё нет |
| `GET /prices/by-date?ticker=btc_usd&on=2026-10-14` | Все точки за UTC-календарную дату |
| `GET /health` | Проверка доступности процесса API |

Примеры:

```bash
curl 'http://localhost:8000/prices?ticker=btc_usd'
curl 'http://localhost:8000/prices/latest?ticker=eth_usd'
curl 'http://localhost:8000/prices/by-date?ticker=btc_usd&on=2026-10-14'
```

Запись цены имеет формат:

```json
{"id": 1, "ticker": "btc_usd", "price": 65000.5, "timestamp": 1791972000}
```

## Запуск через Docker Compose

Требуются Docker и Docker Compose v2.

```bash
cp .env.example .env
# При желании замените POSTGRES_PASSWORD в .env
docker compose up --build
```

Compose дождётся готовности PostgreSQL и Redis, применит `alembic upgrade head`, затем поднимет API под Gunicorn с Uvicorn worker, worker и Beat. Gunicorn запускается с `exec`, поэтому он становится главным процессом контейнера и корректно получает сигналы остановки. API будет доступно на <http://localhost:8000>; Swagger UI — <http://localhost:8000/docs>. Первая задача планируется Celery Beat при старте и затем повторяется с минутным интервалом. Данные PostgreSQL сохраняются в volume `postgres_data`.

Остановка:

```bash
docker compose down
# Для удаления локальных данных БД дополнительно: docker compose down -v
```

## Локальная разработка

Нужны Python 3.11+ и доступные PostgreSQL и Redis. Создайте окружение и установите зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
```

При запуске приложения на хосте укажите в `.env` адреса `localhost` для PostgreSQL и Redis (пример `DATABASE_URL=postgresql+psycopg://prices:change-me@localhost:5432/prices`). Примените миграции, затем запустите процессы в отдельных терминалах:

```bash
alembic upgrade head
uvicorn app.main:app --reload
celery -A app.worker.celery_app worker --loglevel=INFO
celery -A app.worker.celery_app beat --loglevel=INFO
```

## Тесты и качество кода

```bash
python -m pytest
ruff check .
```

Тесты создают таблицы в SQLite in-memory и проверяют выдачу истории, последнюю цену, фильтрацию по UTC-дате и валидацию обязательного/поддерживаемого тикера. GitHub Actions запускает обе проверки для каждого push и pull request.

## Design decisions

- **UTC и UNIX timestamp.** Данные хранятся как целые секунды Unix; календарный фильтр трактует дату как UTC и использует полуоткрытый диапазон `[00:00, 00:00 следующего дня)`, что исключает ошибки на границе суток.
- **Только индексные тикеры.** Разрешены `btc_usd` и `eth_usd`, соответствующие `index_name` публичного метода Deribit. Неподдерживаемое значение возвращает `422` вместо неоднозначного пустого результата.
- **Одна запись на полученный тикер и минуту.** Сохраняется каждая выборка, без обновления старой строки; это оставляет историю наблюдений доступной через API. UNIX timestamp назначается на одну пару собранных значений.
- **Celery для планирования.** Celery Beat ставит задачу раз в 60 секунд, worker выполняет сетевой запрос и запись. Redis отделяет расписание и выполнение от HTTP процесса; `aiohttp` асинхронно запрашивает оба индекса.
- **Слои приложения.** Маршруты, бизнес-сервис, репозиторий и внешний клиент разделены для независимой проверки и замены инфраструктуры. Сессия SQLAlchemy передаётся зависимостью запроса, а не хранится глобально.
- **PostgreSQL в Compose, SQLite в тестах.** Производственная схема мигрируется Alembic; тесты используют изолированную in-memory SQLite и не требуют работающего сервера БД.
- **Индекс для чтения истории.** Составной индекс `(ticker, timestamp)` ускоряет основные фильтры API и выбор последней точки.

## Структура проекта

```text
app/
  api/routes.py       HTTP endpoints
  clients.py          Deribit aiohttp client
  core/config.py      Environment configuration
  db/                 SQLAlchemy base and session dependency
  models.py           Price history table
  repositories.py     Database access
  services.py         Ticker validation and use cases
  worker.py           Celery worker and periodic task
  main.py             FastAPI application
migrations/           Alembic configuration and revisions
tests/                API tests using in-memory SQLite
.github/workflows/    pytest and Ruff CI
```
