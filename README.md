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

## Test Coverage

The repository now includes:
- Unit tests for status transitions and role access checks.
- Unit tests for AML provider behavior.
- API integration-style tests using FastAPI `TestClient` with an async fake DB.
- Bot handler tests for command validation and backend response handling.

Run tests:

```powershell
pytest -q
```

## API curl Examples

Use headers to simulate actor identity/role:

```bash
-H "X-Actor-Id: 101" -H "X-Actor-Role: manager"
```

AML check:

```bash
curl -X POST http://localhost:8000/api/v1/aml/check \
  -H "Content-Type: application/json" \
  -H "X-Actor-Id: 101" \
  -H "X-Actor-Role: manager" \
  -d '{
    "address": "TVjsExampleAddress001",
    "network": "TRON"
  }'
```

Create payment request:

```bash
curl -X POST http://localhost:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -H "X-Actor-Id: 101" \
  -H "X-Actor-Role: manager" \
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
  -H "X-Actor-Id: 101" \
  -H "X-Actor-Role: manager"
```

Approve request (head role):

```bash
curl -X POST http://localhost:8000/api/v1/requests/<REQUEST_ID>/approve \
  -H "Content-Type: application/json" \
  -H "X-Actor-Id: 500" \
  -H "X-Actor-Role: head" \
  -d '{"reason":"Approved after AML review"}'
```

Mark as paid:

```bash
curl -X POST http://localhost:8000/api/v1/requests/<REQUEST_ID>/mark-paid \
  -H "Content-Type: application/json" \
  -H "X-Actor-Id: 500" \
  -H "X-Actor-Role: head" \
  -d '{"tx_hash":"TRON_TX_HASH_HERE"}'
```

## AML Business Logic (Current MVP)

1. A manager or analyst submits wallet address + network to `/aml/check`.
2. The API uses configured provider (`AML_PROVIDER=mock|http`).
3. Provider returns `risk_score`, `risk_level`, and risk categories.
4. AML result is saved in `wallet_checks` and linked to payment request by `aml_check_id`.
5. Request lifecycle enforces status transitions:
   - `draft -> pending -> approved -> paid`
   - `pending -> rejected`
6. Role restrictions are enforced by header-based RBAC:
   - manager/admin: create + submit
   - head/admin: approve + mark-paid
   - analyst: read + AML checks
7. Every status change writes to `status_history` and `audit_logs`.

## CI/CD

### CI (GitHub Actions)

Workflow file: `.github/workflows/ci.yml`

- Trigger: push (all branches), pull request to `main`
- Jobs:
  - `test`: install deps, compile check, run unit/integration tests
  - `build-images`: build API and bot Docker images (no push)

### CD (GitHub Actions)

Workflow file: `.github/workflows/cd.yml`

- Trigger: push to `main`, manual dispatch
- Action: build and publish Docker images to GHCR:
  - `ghcr.io/<owner>/tronsecurecompliance-api`
  - `ghcr.io/<owner>/tronsecurecompliance-bot`

Required repository setting:
- Actions permissions should be set to `Read and write permissions`.

## Roadmap

1. Replace header-based RBAC with secure auth (JWT/session + Telegram identity mapping).
2. Add real AML provider adapters (Chainalysis/Crystal/AMLBot) with retries, circuit breaker, and provider fallback.
3. Add DB-backed integration tests in CI with ephemeral Postgres service.
4. Add policy engine for auto-reject / override flow on high-risk wallets.
5. Add notification and escalation channels (Telegram + email/webhooks).
6. Add immutable audit export and compliance reporting package.
7. Add deployment manifests (Kubernetes/Helm/Terraform) and environment promotion gates.

## Key Files

- `sql/schema.sql` - SQL DDL
- `alembic/versions/0001_initial.py` - initial migration
- `specs/openapi.yaml` - OpenAPI 3.0
- `app/` - FastAPI backend
- `bot/bot.py` - Telegram bot
- `.github/workflows/ci.yml` - CI pipeline
- `.github/workflows/cd.yml` - CD pipeline
