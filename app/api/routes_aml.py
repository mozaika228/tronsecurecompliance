from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_actor_id, get_actor_role, require_role
from app.api.schemas import AmlCheckRequest, AmlCheckResponse
from app.db.models import UserRole, WalletCheck
from app.db.session import get_db
from app.services.aml_provider import get_aml_provider

router = APIRouter(tags=["AML"])


@router.post("/aml/check", response_model=AmlCheckResponse)
async def run_aml_check(
    payload: AmlCheckRequest,
    db: AsyncSession = Depends(get_db),
    actor_id: int = Depends(get_actor_id),
    actor_role: UserRole = Depends(get_actor_role),
) -> AmlCheckResponse:
    require_role({UserRole.manager, UserRole.analyst, UserRole.head, UserRole.admin}, actor_role)
    aml_provider = get_aml_provider()
    risk_score, risk_level, categories, raw_report = await aml_provider.check(payload.address, payload.network)
    check = WalletCheck(
        address=payload.address,
        network=payload.network,
        provider=aml_provider.provider_name,
        risk_score=risk_score,
        risk_level=risk_level,
        categories_json=[c.model_dump() for c in categories],
        raw_report_json=raw_report,
        checked_by=actor_id,
    )
    db.add(check)
    await db.commit()
    await db.refresh(check)
    return AmlCheckResponse(
        check_id=check.id,
        risk_score=float(check.risk_score),
        risk_level=check.risk_level,
        categories=categories,
        checked_at=check.checked_at,
    )
