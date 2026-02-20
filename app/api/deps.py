from fastapi import Header, HTTPException, status

from app.db.models import UserRole


def get_actor_id(x_actor_id: int | None = Header(default=None)) -> int:
    if x_actor_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Actor-Id header")
    return x_actor_id


def get_actor_role(x_actor_role: str | None = Header(default=None)) -> UserRole:
    if not x_actor_role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Actor-Role header")
    try:
        return UserRole(x_actor_role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role header") from exc


def require_role(allowed: set[UserRole], role: UserRole) -> None:
    if role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden for current role")
