import pytest
from fastapi import HTTPException

from app.api.deps import get_actor_role, require_role
from app.db.models import UserRole


def test_get_actor_role_valid() -> None:
    assert get_actor_role("manager") == UserRole.manager


def test_get_actor_role_invalid() -> None:
    with pytest.raises(HTTPException) as exc:
        get_actor_role("wrong")
    assert exc.value.status_code == 400


def test_require_role_forbidden() -> None:
    with pytest.raises(HTTPException) as exc:
        require_role({UserRole.admin}, UserRole.manager)
    assert exc.value.status_code == 403
