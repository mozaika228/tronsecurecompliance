from app.api.routes_requests import ensure_transition
from app.db.models import RequestStatus


def test_valid_transitions() -> None:
    ensure_transition(RequestStatus.draft, RequestStatus.pending)
    ensure_transition(RequestStatus.pending, RequestStatus.approved)
    ensure_transition(RequestStatus.pending, RequestStatus.rejected)
    ensure_transition(RequestStatus.approved, RequestStatus.paid)
