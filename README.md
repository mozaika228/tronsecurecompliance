# tronsecurecompliance

MVP scaffold for:
- automated AML wallet checks
- crypto payment request management
- Telegram-based approval workflows

## Local Setup

1. Create `.env` from `.env.example`.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Apply database migrations:

```powershell
alembic upgrade head
```

4. Start API:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Start Telegram bot:

```powershell
python bot/bot.py
```

## Docker Compose

Run Postgres + API:

```powershell
docker compose up --build db api
```

Run bot (optional, requires `BOT_TOKEN`):

```powershell
docker compose --profile bot up --build
```

## Smoke Test

After API startup:

```powershell
python scripts/smoke.py --base-url http://localhost:8000
```

## CI/CD

### CI (GitHub Actions)
- Trigger: push (all branches) and pull request to `main`
- Steps:
  - install Python dependencies
  - run `python -m compileall app bot scripts`
  - run `pytest -q`

Workflow file: `.github/workflows/ci.yml`

### CD (GitHub Actions)
- Trigger: push to `main` and manual dispatch
- Action: build and publish Docker images to GHCR
  - `ghcr.io/<owner>/tronsecurecompliance-api`
  - `ghcr.io/<owner>/tronsecurecompliance-bot`

Workflow file: `.github/workflows/cd.yml`

Required permissions/secrets:
- No extra secrets required for GHCR when using built-in `GITHUB_TOKEN`
- Repository Actions permissions should allow `Read and write permissions`

## Key Files

- `sql/schema.sql` - SQL DDL
- `alembic/versions/0001_initial.py` - initial migration
- `specs/openapi.yaml` - OpenAPI 3.0
- `app/` - FastAPI backend
- `bot/bot.py` - Telegram bot
- `.github/workflows/ci.yml` - CI pipeline
- `.github/workflows/cd.yml` - CD pipeline
