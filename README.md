# tronsecurecompliance

MVP каркас для:
- AML-проверок адресов
- управления заявками на криптоплатежи
- согласования в Telegram

## Локальный запуск

1. Создайте `.env` из `.env.example`.
2. Установите зависимости:

```powershell
pip install -r requirements.txt
```

3. Поднимите схему БД миграциями:

```powershell
alembic upgrade head
```

4. Запустите API:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Запустите Telegram-бота:

```powershell
python bot/bot.py
```

## Docker Compose

Запуск Postgres + API:

```powershell
docker compose up --build db api
```

Запуск бота (опционально, нужен `BOT_TOKEN`):

```powershell
docker compose --profile bot up --build
```

## Smoke-тест

После старта API выполните:

```powershell
python scripts/smoke.py --base-url http://localhost:8000
```

## Основные файлы

- `sql/schema.sql` - SQL DDL
- `alembic/versions/0001_initial.py` - initial migration
- `specs/openapi.yaml` - OpenAPI 3.0
- `app/` - backend FastAPI
- `bot/bot.py` - Telegram bot
