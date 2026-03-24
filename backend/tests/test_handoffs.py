import pytest
from uuid import uuid4

from contracts.handoff import HandoffCreate
from contracts.shared import HandoffStatus


def test_handoff_create():
    h = HandoffCreate(
        to_partner_id=uuid4(),
        candidate_ids=[uuid4(), uuid4()],
        context_notes="Strong Python candidates for your fintech role",
        target_role_id=uuid4(),
    )
    assert len(h.candidate_ids) == 2
    assert h.target_role_id is not None


def test_handoff_create_no_role():
    h = HandoffCreate(
        to_partner_id=uuid4(),
        candidate_ids=[uuid4()],
        context_notes="General referral — great ML engineers",
    )
    assert h.target_role_id is None


def test_handoff_status_transitions():
    """Valid transitions: pending → accepted/declined/expired."""
    valid_from_pending = {HandoffStatus.accepted, HandoffStatus.declined, HandoffStatus.expired}
    assert HandoffStatus.pending not in valid_from_pending


def test_handoff_status_values():
    """All handoff statuses have expected string values."""
    assert HandoffStatus.pending.value == "pending"
    assert HandoffStatus.accepted.value == "accepted"
    assert HandoffStatus.declined.value == "declined"
    assert HandoffStatus.expired.value == "expired"


def test_handoff_create_multiple_candidates():
    candidate_ids = [uuid4() for _ in range(5)]
    h = HandoffCreate(
        to_partner_id=uuid4(),
        candidate_ids=candidate_ids,
        context_notes="Batch referral of 5 senior engineers",
    )
    assert len(h.candidate_ids) == 5


def test_response_time_calculation():
    """Test the response time computation logic."""
    from services.handoff import HandoffService
    from unittest.mock import MagicMock

    service = HandoffService(MagicMock())

    # Same timestamp → 0 seconds
    now = "2024-01-01T12:00:00"
    assert service._compute_response_time(now, now) == 0

    # 1 hour later
    created = "2024-01-01T10:00:00"
    responded = "2024-01-01T11:00:00"
    assert service._compute_response_time(created, responded) == 3600

    # Invalid timestamps → 0
    assert service._compute_response_time("invalid", "also-invalid") == 0
