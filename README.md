# tronsecurecompliance

MVP scaffold for:
- automated AML wallet checks
- crypto payment request management
- Telegram-based approval workflows

## License

This project is licensed under the MIT License. See `LICENSE`.

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

5. Create users in DB (required for Telegram auth).
6. Start Telegram bot:

```powershell
python bot/bot.py
```

## Telegram Auth Model

Backend now resolves user and role by `telegram_id` from `users` table via header `X-Telegram-Id`.

- Bot sends only `X-Telegram-Id`.
- Backend loads user from DB and enforces RBAC by stored `role`.
- If user is missing/inactive, request is rejected.

### Bootstrap first admin user

Use one legacy call with manual actor headers, then switch to Telegram-based flow:

```bash
curl -X POST http://localhost:8000/api/v1/admin/users \
  -H "Content-Type: application/json" \
  -H "X-Actor-Id: 1" \
  -H "X-Actor-Role: admin" \
  -d '{
    "telegram_id": 123456789,
    "full_name": "Main Admin",
    "role": "admin"
  }'
```

After this, use `X-Telegram-Id: 123456789` for admin calls.

## Docker Compose

Run Postgres + API:

```powershell
docker compose up --build db api
```

Run bot (optional, requires `BOT_TOKEN`):

```powershell
docker compose --profile bot up --build
```

## Tests

Run tests:

```powershell
pytest -q
```

Coverage includes:
- status transition and RBAC checks
- AML provider behavior
- API handler tests (async with fake DB)
- bot command handler tests

## API curl Examples

Preferred header:

```bash
-H "X-Telegram-Id: 123456789"
```

AML check:

```bash
curl -X POST http://localhost:8000/api/v1/aml/check \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Id: 123456789" \
  -d '{
    "address": "TVjsExampleAddress001",
    "network": "TRON"
  }'
```

Create payment request:

```bash
curl -X POST http://localhost:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Id: 123456789" \
  -d '{
    "address": "TVjsExampleAddress001",
    "network": "TRON",
    "asset": "USDT",
    "amount": "150.00",
    "comment": "Vendor payout",
    "aml_check_id": "<CHECK_ID_FROM_PREVIOUS_STEP>"
  }'
```

Submit request:

```bash
curl -X POST http://localhost:8000/api/v1/requests/<REQUEST_ID>/submit \
  -H "X-Telegram-Id: 123456789"
```

Approve request (head role):

```bash
curl -X POST http://localhost:8000/api/v1/requests/<REQUEST_ID>/approve \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Id: 987654321" \
  -d '{"reason":"Approved after AML review"}'
```

Mark as paid:

```bash
curl -X POST http://localhost:8000/api/v1/requests/<REQUEST_ID>/mark-paid \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Id: 987654321" \
  -d '{"tx_hash":"TRON_TX_HASH_HERE"}'
```

## CI/CD

- CI: `.github/workflows/ci.yml` (compile, tests, docker build)
- CD: `.github/workflows/cd.yml` (publish images to GHCR on `main`)

## Key Files

- `app/api/deps.py` - Telegram-based actor resolution and RBAC
- `app/api/routes_admin.py` - user creation and role management
- `bot/bot.py` - Telegram bot client
- `specs/openapi.yaml` - API spec
