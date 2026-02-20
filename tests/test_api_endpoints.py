import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.routes_aml import run_aml_check
from app.api.routes_requests import approve_request, create_request, submit_request
from app.api.schemas import AmlCheckRequest, RequestCreate, RiskCategory
from app.db.models import RequestStatus, RiskLevel, UserRole


class FakeExecResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        return self

    def all(self):
        return self._value or []


class FakeSession:
    def __init__(self, execute_results):
        self._results = list(execute_results)
        self.added = []

    async def execute(self, _stmt):
        value = self._results.pop(0) if self._results else None
        return FakeExecResult(value)

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        return None

    async def commit(self):
        return None

    async def refresh(self, obj):
        now = datetime.now(timezone.utc)
        if getattr(obj, "id", None) is None:
            obj.id = uuid4()
        if getattr(obj, "created_at", None) is None:
            obj.created_at = now
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = now
        if getattr(obj, "checked_at", None) is None:
            obj.checked_at = now


class FakeProvider:
    provider_name = "mock"

    async def check(self, address: str, network: str):
        categories = [RiskCategory(name="General", score=12.5)]
        return 12.5, RiskLevel.low, categories, {
            "address": address,
            "network": network,
            "risk_score": 12.5,
            "risk_level": "low",
            "categories": [{"name": "General", "score": 12.5}],
        }


def test_run_aml_check_success(monkeypatch) -> None:
    fake_db = FakeSession([])
    monkeypatch.setattr("app.api.routes_aml.get_aml_provider", lambda: FakeProvider())
    payload = AmlCheckRequest(address="TVjs1", network="TRON")

    res = asyncio.run(run_aml_check(payload=payload, db=fake_db, actor_id=101, actor_role=UserRole.manager))
    assert res.risk_level == RiskLevel.low


def test_create_request_requires_aml_check() -> None:
    fake_db = FakeSession([None])
    payload = RequestCreate(
        address="TVjs1",
        network="TRON",
        asset="USDT",
        amount=Decimal("10.0"),
        aml_check_id=uuid4(),
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(create_request(payload=payload, db=fake_db, actor_id=101, actor_role=UserRole.manager))
    assert exc.value.status_code == 404


def test_create_request_success() -> None:
    wallet_check = SimpleNamespace(id=uuid4())
    fake_db = FakeSession([wallet_check])
    payload = RequestCreate(
        address="TVjs1",
        network="TRON",
        asset="USDT",
        amount=Decimal("10.0"),
        aml_check_id=wallet_check.id,
        comment="test",
    )

    res = asyncio.run(create_request(payload=payload, db=fake_db, actor_id=101, actor_role=UserRole.manager))
    assert res.status == RequestStatus.draft
    assert Decimal(res.amount) == Decimal("10.0")


def test_submit_forbidden_for_head() -> None:
    with pytest.raises(HTTPException) as exc:
        asyncio.run(submit_request(request_id=uuid4(), db=FakeSession([]), actor_id=500, actor_role=UserRole.head))
    assert exc.value.status_code == 403


def test_approve_invalid_transition() -> None:
    payment = SimpleNamespace(
        id=uuid4(),
        status=RequestStatus.draft,
        approved_by=None,
        approved_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        request_no="PAY-202602-AAAA",
        creator_id=101,
        address="TVjs1",
        network="TRON",
        asset="USDT",
        amount=Decimal("10.0"),
        comment=None,
        attachment_url=None,
        aml_check_id=uuid4(),
        tx_hash=None,
    )
    fake_db = FakeSession([payment])

    with pytest.raises(HTTPException) as exc:
        asyncio.run(approve_request(request_id=payment.id, payload=None, db=fake_db, actor_id=500, actor_role=UserRole.head))
    assert exc.value.status_code == 409
