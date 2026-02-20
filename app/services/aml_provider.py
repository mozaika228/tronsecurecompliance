import random
from typing import Protocol

import httpx

from app.api.schemas import RiskCategory
from app.config import settings
from app.db.models import RiskLevel


class AmlProvider(Protocol):
    provider_name: str

    async def check(self, address: str, network: str) -> tuple[float, RiskLevel, list[RiskCategory], dict]:
        ...


class MockAmlProvider:
    provider_name = "mock"

    async def check(self, address: str, network: str) -> tuple[float, RiskLevel, list[RiskCategory], dict]:
        seed = sum(ord(ch) for ch in address + network)
        random.seed(seed)
        risk_score = round(random.uniform(5, 95), 2)
        if risk_score < 35:
            risk_level = RiskLevel.low
        elif risk_score < 70:
            risk_level = RiskLevel.medium
        else:
            risk_level = RiskLevel.high
        categories = [
            RiskCategory(name="Sanctions", score=round(min(100, risk_score + random.uniform(-10, 10)), 2)),
            RiskCategory(name="Scam", score=round(min(100, risk_score + random.uniform(-15, 15)), 2)),
        ]
        raw_report = {
            "address": address,
            "network": network,
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "categories": [category.model_dump() for category in categories],
        }
        return risk_score, risk_level, categories, raw_report


class HttpAmlProvider:
    provider_name = "http"

    def __init__(self, base_url: str, api_key: str, timeout_s: float, check_path: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_s
        self._check_path = check_path

    async def check(self, address: str, network: str) -> tuple[float, RiskLevel, list[RiskCategory], dict]:
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        payload = {"address": address, "network": network}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base_url}{self._check_path}", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        risk_score = float(data.get("risk_score", 0))
        raw_level = str(data.get("risk_level", "low")).lower()
        if raw_level not in {"low", "medium", "high"}:
            if risk_score < 35:
                raw_level = "low"
            elif risk_score < 70:
                raw_level = "medium"
            else:
                raw_level = "high"
        risk_level = RiskLevel(raw_level)

        raw_categories = data.get("categories", [])
        categories: list[RiskCategory] = []
        for entry in raw_categories:
            try:
                categories.append(RiskCategory(name=str(entry["name"]), score=float(entry["score"])))
            except Exception:
                continue

        if not categories:
            categories = [RiskCategory(name="General", score=risk_score)]

        raw_report = data if isinstance(data, dict) else {"raw": data}
        return risk_score, risk_level, categories, raw_report


def get_aml_provider() -> AmlProvider:
    provider_name = settings.aml_provider.lower().strip()
    if provider_name == "http":
        return HttpAmlProvider(
            base_url=settings.aml_http_base_url,
            api_key=settings.aml_http_api_key,
            timeout_s=settings.aml_http_timeout_s,
            check_path=settings.aml_http_check_path,
        )
    return MockAmlProvider()
