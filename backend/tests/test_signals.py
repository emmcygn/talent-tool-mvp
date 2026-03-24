from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from contracts.shared import SignalType, UserRole
from signals.tracker import SignalTracker


@pytest.fixture
def mock_supabase():
    mock = MagicMock()
    mock_table = MagicMock()
    mock.table.return_value = mock_table
    mock_insert = MagicMock()
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])
    return mock


@pytest.fixture
def tracker(mock_supabase):
    return SignalTracker(mock_supabase)


@pytest.mark.asyncio
async def test_emit_signal(tracker, mock_supabase):
    result = await tracker.emit(
        event_type=SignalType.candidate_viewed,
        actor_id=uuid4(),
        actor_role=UserRole.talent_partner,
        entity_type="candidate",
        entity_id=uuid4(),
        metadata={"time_spent_seconds": 45},
    )
    assert result is not None
    mock_supabase.table.assert_called_with("signals")


@pytest.mark.asyncio
async def test_emit_with_string_types(tracker, mock_supabase):
    result = await tracker.emit(
        event_type="candidate_viewed",
        actor_id=str(uuid4()),
        actor_role="talent_partner",
        entity_type="candidate",
        entity_id=str(uuid4()),
    )
    assert result is not None


@pytest.mark.asyncio
async def test_emit_batch(tracker, mock_supabase):
    signals = [
        {
            "event_type": SignalType.candidate_viewed,
            "actor_id": uuid4(),
            "actor_role": UserRole.talent_partner,
            "entity_type": "candidate",
            "entity_id": uuid4(),
        },
        {
            "event_type": SignalType.candidate_shortlisted,
            "actor_id": uuid4(),
            "actor_role": UserRole.client,
            "entity_type": "candidate",
            "entity_id": uuid4(),
        },
    ]
    count = await tracker.emit_batch(signals)
    assert count == 2
