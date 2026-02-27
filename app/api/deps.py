from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, UserRole
from app.db.session import get_db


async def get_actor(
    db: AsyncSession = Depends(get_db),
    x_telegram_id: int | None = Header(default=None),
    x_actor_id: int | None = Header(default=None),
    x_actor_role: str | None = Header(default=None),
) -> User:
    # Preferred mode for production: lookup user by Telegram ID from DB.
    if x_telegram_id is not None:
        user = (await db.execute(select(User).where(User.telegram_id == x_telegram_id))).scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Telegram user is not registered or inactive",
            )
        return user

    # Legacy fallback for local scripts and bootstrap flows.
    if x_actor_id is None or not x_actor_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Telegram-Id header",
        )
    try:
        role = UserRole(x_actor_role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role header") from exc
    return User(id=x_actor_id, telegram_id=0, full_name="legacy-actor", role=role, is_active=True)


async def get_actor_id(actor: User = Depends(get_actor)) -> int:
    return actor.id


async def get_actor_role(actor: User = Depends(get_actor)) -> UserRole:
    return actor.role


def require_role(allowed: set[UserRole], role: UserRole) -> None:
    if role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden for current role")
