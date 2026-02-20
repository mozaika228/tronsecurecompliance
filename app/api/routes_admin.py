from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_actor_role, require_role
from app.api.schemas import RoleUpdatePayload, UserResponse
from app.db.models import User, UserRole
from app.db.session import get_db

router = APIRouter(tags=["Admin"])


@router.post("/admin/users/{user_id}/role", response_model=UserResponse)
async def update_role(
    user_id: int,
    payload: RoleUpdatePayload,
    db: AsyncSession = Depends(get_db),
    actor_role: UserRole = Depends(get_actor_role),
) -> UserResponse:
    require_role({UserRole.admin}, actor_role)
    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.role = payload.role
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)
