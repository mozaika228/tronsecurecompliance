import asyncio

from app.db.models import RiskLevel
from app.services.aml_provider import MockAmlProvider


def test_mock_aml_provider_is_deterministic() -> None:
    provider = MockAmlProvider()
    a = asyncio.run(provider.check("TVjsDeterministic", "TRON"))
    b = asyncio.run(provider.check("TVjsDeterministic", "TRON"))

    assert a[0] == b[0]
    assert a[1] == b[1]
    assert a[2][0].name == "Sanctions"
    assert a[1] in {RiskLevel.low, RiskLevel.medium, RiskLevel.high}
