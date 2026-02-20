import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_actor_id, get_actor_role, require_role
from app.api.schemas import DecisionPayload, MarkPaidPayload, RequestCreate, RequestResponse, StatusHistoryItem
from app.db.models import AuditLog, PaymentRequest, RequestStatus, StatusHistory, UserRole, WalletCheck
from app.db.session import get_db

router = APIRouter(tags=["Requests"])


def build_request_no() -> str:
    now = datetime.utcnow()
    return f"PAY-{now:%Y%m}-{uuid.uuid4().hex[:4].upper()}"


def ensure_transition(old_status: RequestStatus, new_status: RequestStatus) -> None:
    allowed = {
        RequestStatus.draft: {RequestStatus.pending, RequestStatus.rejected},
        RequestStatus.pending: {RequestStatus.approved, RequestStatus.rejected},
        RequestStatus.approved: {RequestStatus.paid},
        RequestStatus.rejected: set(),
        RequestStatus.paid: set(),
    }
    if new_status not in allowed[old_status]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid transition: {old_status.value} -> {new_status.value}",
        )


async def log_status(
    db: AsyncSession,
    request_id: uuid.UUID,
    old_status: RequestStatus | None,
    new_status: RequestStatus,
    actor_id: int,
    reason: str | None = None,
) -> None:
    db.add(
        StatusHistory(
            request_id=request_id,
            old_status=old_status,
            new_status=new_status,
            actor_id=actor_id,
            reason=reason,
        )
    )
    db.add(
        AuditLog(
            actor_id=actor_id,
            action="request_status_changed",
            entity_type="payment_request",
            entity_id=str(request_id),
            payload_json={"old_status": old_status.value if old_status else None, "new_status": new_status.value, "reason": reason},
        )
    )


@router.post("/requests", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
    payload: RequestCreate,
    db: AsyncSession = Depends(get_db),
    actor_id: int = Depends(get_actor_id),
    actor_role: UserRole = Depends(get_actor_role),
) -> RequestResponse:
    require_role({UserRole.manager, UserRole.admin}, actor_role)
    check = (await db.execute(select(WalletCheck).where(WalletCheck.id == payload.aml_check_id))).scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AML check not found")
    request = PaymentRequest(
        request_no=build_request_no(),
        creator_id=actor_id,
        address=payload.address,
        network=payload.network,
        asset=payload.asset,
        amount=payload.amount,
        comment=payload.comment,
        attachment_url=payload.attachment_url,
        aml_check_id=payload.aml_check_id,
        status=RequestStatus.draft,
    )
    db.add(request)
    await db.flush()
    await log_status(db, request.id, None, RequestStatus.draft, actor_id, "created")
    await db.commit()
    await db.refresh(request)
    return RequestResponse.model_validate(request)


@router.get("/requests", response_model=list[RequestResponse])
async def list_requests(
    status: RequestStatus | None = None,
    db: AsyncSession = Depends(get_db),
    actor_role: UserRole = Depends(get_actor_role),
) -> list[RequestResponse]:
    require_role({UserRole.manager, UserRole.head, UserRole.analyst, UserRole.admin}, actor_role)
    stmt = select(PaymentRequest).order_by(PaymentRequest.created_at.desc())
    if status:
        stmt = stmt.where(PaymentRequest.status == status)
    rows = (await db.execute(stmt)).scalars().all()
    return [RequestResponse.model_validate(row) for row in rows]


@router.get("/requests/{request_id}", response_model=RequestResponse)
async def get_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor_role: UserRole = Depends(get_actor_role),
) -> RequestResponse:
    require_role({UserRole.manager, UserRole.head, UserRole.analyst, UserRole.admin}, actor_role)
    item = (await db.execute(select(PaymentRequest).where(PaymentRequest.id == request_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return RequestResponse.model_validate(item)


@router.post("/requests/{request_id}/submit", response_model=RequestResponse)
async def submit_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor_id: int = Depends(get_actor_id),
    actor_role: UserRole = Depends(get_actor_role),
) -> RequestResponse:
    require_role({UserRole.manager, UserRole.admin}, actor_role)
    item = (await db.execute(select(PaymentRequest).where(PaymentRequest.id == request_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    old = item.status
    ensure_transition(old, RequestStatus.pending)
    item.status = RequestStatus.pending
    await log_status(db, item.id, old, RequestStatus.pending, actor_id, "submitted")
    await db.commit()
    await db.refresh(item)
    return RequestResponse.model_validate(item)


@router.post("/requests/{request_id}/approve", response_model=RequestResponse)
async def approve_request(
    request_id: uuid.UUID,
    payload: DecisionPayload | None = None,
    db: AsyncSession = Depends(get_db),
    actor_id: int = Depends(get_actor_id),
    actor_role: UserRole = Depends(get_actor_role),
) -> RequestResponse:
    require_role({UserRole.head, UserRole.admin}, actor_role)
    item = (await db.execute(select(PaymentRequest).where(PaymentRequest.id == request_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    old = item.status
    ensure_transition(old, RequestStatus.approved)
    item.status = RequestStatus.approved
    item.approved_by = actor_id
    item.approved_at = datetime.utcnow()
    await log_status(db, item.id, old, RequestStatus.approved, actor_id, payload.reason if payload else None)
    await db.commit()
    await db.refresh(item)
    return RequestResponse.model_validate(item)


@router.post("/requests/{request_id}/reject", response_model=RequestResponse)
async def reject_request(
    request_id: uuid.UUID,
    payload: DecisionPayload,
    db: AsyncSession = Depends(get_db),
    actor_id: int = Depends(get_actor_id),
    actor_role: UserRole = Depends(get_actor_role),
) -> RequestResponse:
    require_role({UserRole.head, UserRole.admin, UserRole.manager}, actor_role)
    item = (await db.execute(select(PaymentRequest).where(PaymentRequest.id == request_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    old = item.status
    ensure_transition(old, RequestStatus.rejected)
    item.status = RequestStatus.rejected
    item.rejection_reason = payload.reason
    await log_status(db, item.id, old, RequestStatus.rejected, actor_id, payload.reason)
    await db.commit()
    await db.refresh(item)
    return RequestResponse.model_validate(item)


@router.post("/requests/{request_id}/mark-paid", response_model=RequestResponse)
async def mark_paid(
    request_id: uuid.UUID,
    payload: MarkPaidPayload,
    db: AsyncSession = Depends(get_db),
    actor_id: int = Depends(get_actor_id),
    actor_role: UserRole = Depends(get_actor_role),
) -> RequestResponse:
    require_role({UserRole.head, UserRole.admin}, actor_role)
    item = (await db.execute(select(PaymentRequest).where(PaymentRequest.id == request_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    old = item.status
    ensure_transition(old, RequestStatus.paid)
    item.status = RequestStatus.paid
    item.tx_hash = payload.tx_hash
    item.paid_at = datetime.utcnow()
    await log_status(db, item.id, old, RequestStatus.paid, actor_id, "marked paid")
    await db.commit()
    await db.refresh(item)
    return RequestResponse.model_validate(item)


@router.get("/requests/{request_id}/history", response_model=list[StatusHistoryItem])
async def request_history(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor_role: UserRole = Depends(get_actor_role),
) -> list[StatusHistoryItem]:
    require_role({UserRole.manager, UserRole.head, UserRole.analyst, UserRole.admin}, actor_role)
    rows = (
        await db.execute(select(StatusHistory).where(StatusHistory.request_id == request_id).order_by(StatusHistory.created_at.asc()))
    ).scalars().all()
    return [StatusHistoryItem.model_validate(row) for row in rows]
