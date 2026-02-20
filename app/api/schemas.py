import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import RequestStatus, RiskLevel, UserRole


class RiskCategory(BaseModel):
    name: str
    score: float


class AmlCheckRequest(BaseModel):
    address: str
    network: str = Field(pattern="^TRON$")


class AmlCheckResponse(BaseModel):
    check_id: uuid.UUID
    risk_score: float
    risk_level: RiskLevel
    categories: list[RiskCategory]
    checked_at: datetime


class RequestCreate(BaseModel):
    address: str
    network: str = Field(pattern="^TRON$")
    asset: str = Field(pattern="^USDT$")
    amount: Decimal
    comment: str | None = None
    attachment_url: str | None = None
    aml_check_id: uuid.UUID


class RequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    request_no: str
    creator_id: int
    address: str
    network: str
    asset: str
    amount: Decimal
    comment: str | None
    attachment_url: str | None
    aml_check_id: uuid.UUID
    status: RequestStatus
    tx_hash: str | None
    created_at: datetime
    updated_at: datetime


class DecisionPayload(BaseModel):
    reason: str | None = None


class MarkPaidPayload(BaseModel):
    tx_hash: str


class StatusHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: uuid.UUID
    old_status: RequestStatus | None
    new_status: RequestStatus
    actor_id: int | None
    reason: str | None
    created_at: datetime


class RoleUpdatePayload(BaseModel):
    role: UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    full_name: str
    role: UserRole
