import pytest
from fastapi import HTTPException

from app.api.deps import require_role
from app.db.models import UserRole


def test_require_role_forbidden() -> None:
    with pytest.raises(HTTPException) as exc:
        require_role({UserRole.admin}, UserRole.manager)
    assert exc.value.status_code == 403
