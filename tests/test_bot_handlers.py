import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.bot import aml_check, build_headers, new_request


class DummyResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


class DummyClient:
    def __init__(self, response: DummyResponse):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, *args, **kwargs):
        return self._response


def _update(user_id: int = 1):
    return SimpleNamespace(
        effective_user=SimpleNamespace(id=user_id),
        message=SimpleNamespace(reply_text=AsyncMock()),
    )


def test_build_headers() -> None:
    headers = build_headers(_update(42))
    assert headers["X-Telegram-Id"] == "42"


def test_aml_check_usage() -> None:
    update = _update()
    ctx = SimpleNamespace(args=[])

    asyncio.run(aml_check(update, ctx))
    update.message.reply_text.assert_awaited_once()


def test_aml_check_success(monkeypatch) -> None:
    update = _update()
    ctx = SimpleNamespace(args=["TVjs1"])
    payload = {"risk_level": "low", "risk_score": 10, "check_id": "abc"}
    monkeypatch.setattr("bot.bot.httpx.AsyncClient", lambda timeout=20: DummyClient(DummyResponse(200, payload=payload)))

    asyncio.run(aml_check(update, ctx))
    msg = update.message.reply_text.await_args.args[0]
    assert "risk_level=low" in msg


def test_new_request_usage() -> None:
    update = _update()
    ctx = SimpleNamespace(args=["TVjs1"])

    asyncio.run(new_request(update, ctx))
    update.message.reply_text.assert_awaited_once()


def test_new_request_success(monkeypatch) -> None:
    update = _update()
    ctx = SimpleNamespace(args=["TVjs1", "100", "00000000-0000-0000-0000-000000000001"])
    payload = {"request_no": "PAY-202602-AAAA", "status": "draft"}
    monkeypatch.setattr("bot.bot.httpx.AsyncClient", lambda timeout=20: DummyClient(DummyResponse(201, payload=payload)))

    asyncio.run(new_request(update, ctx))
    msg = update.message.reply_text.await_args.args[0]
    assert "Created: PAY-202602-AAAA" in msg
