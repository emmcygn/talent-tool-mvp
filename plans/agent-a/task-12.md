# Agent A — Task 12: Signal Tracking + Analytics

## Mission
Build the signal emission service that tracks every key user action and the analytics aggregation layer that powers dashboards with funnel data, trending skills, partner performance, and client engagement metrics.

## Context
This is Day 4. The signal layer is the nervous system of the platform — every meaningful action (candidate viewed, shortlisted, dismissed, handoff sent, quote generated, etc.) emits a signal event. These signals power activity feeds, analytics dashboards, funnel visualizations, and the recommendation engine. This task builds both the emission side and the query/aggregation side.

## Prerequisites
- Task 03 complete (FastAPI skeleton with auth)
- Task 02 complete (Supabase schema with `signals` table)
- `backend/contracts/signal.py` exists with `Signal`, `SignalCreate`, `SignalType`, `UserRole`

## Checklist
- [ ] Create `backend/signals/__init__.py`
- [ ] Create `backend/signals/tracker.py` — signal emission service
- [ ] Create `backend/signals/analytics.py` — analytics aggregation queries
- [ ] Create `backend/api/signals.py` — signal + analytics endpoints
- [ ] Register router in `backend/main.py`
- [ ] Create `backend/tests/test_signals.py` — unit tests
- [ ] Run tests, verify pass
- [ ] Commit: "Agent A Task 12: Signal tracking + analytics"

## Implementation Details

### Signal Tracker (`backend/signals/tracker.py`)

```python
from uuid import UUID, uuid4
from datetime import datetime
from backend.contracts.shared import SignalType, UserRole
from supabase import Client


class SignalTracker:
    """Emits and queries signal events for activity tracking."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def emit(
        self,
        event_type: str | SignalType,
        actor_id: UUID | str,
        actor_role: str | UserRole,
        entity_type: str,
        entity_id: UUID | str,
        metadata: dict | None = None,
    ) -> dict:
        """
        Emit a signal event. This is the core tracking method.
        Called from endpoints, services, and pipelines whenever
        a meaningful action occurs.
        """
        signal_id = uuid4()
        now = datetime.utcnow().isoformat()

        # Normalize enum values to strings
        if isinstance(event_type, SignalType):
            event_type = event_type.value
        if isinstance(actor_role, UserRole):
            actor_role = actor_role.value

        record = {
            "id": str(signal_id),
            "event_type": event_type,
            "actor_id": str(actor_id),
            "actor_role": actor_role,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "metadata": metadata or {},
            "created_at": now,
        }

        result = self.supabase.table("signals").insert(record).execute()
        return result.data[0] if result.data else record

    async def emit_batch(
        self, signals: list[dict]
    ) -> int:
        """Emit multiple signals at once. Used by seed data and bulk operations."""
        records = []
        for s in signals:
            records.append({
                "id": str(uuid4()),
                "event_type": s["event_type"] if isinstance(s["event_type"], str) else s["event_type"].value,
                "actor_id": str(s["actor_id"]),
                "actor_role": s["actor_role"] if isinstance(s["actor_role"], str) else s["actor_role"].value,
                "entity_type": s["entity_type"],
                "entity_id": str(s["entity_id"]),
                "metadata": s.get("metadata", {}),
                "created_at": s.get("created_at", datetime.utcnow().isoformat()),
            })

        if records:
            self.supabase.table("signals").insert(records).execute()

        return len(records)

    async def get_recent(
        self,
        limit: int = 50,
        event_type: str | None = None,
        actor_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        since: datetime | None = None,
    ) -> list[dict]:
        """
        Get recent signals with optional filters.
        Used for activity feeds and real-time updates.
        """
        query = self.supabase.table("signals").select("*") \
            .order("created_at", desc=True) \
            .limit(limit)

        if event_type:
            query = query.eq("event_type", event_type)
        if actor_id:
            query = query.eq("actor_id", str(actor_id))
        if entity_type:
            query = query.eq("entity_type", entity_type)
        if entity_id:
            query = query.eq("entity_id", str(entity_id))
        if since:
            query = query.gte("created_at", since.isoformat())

        result = query.execute()
        return result.data or []

    async def get_signals_for_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        limit: int = 100,
    ) -> list[dict]:
        """Get all signals related to a specific entity (candidate, role, match, etc.)."""
        result = self.supabase.table("signals").select("*") \
            .eq("entity_type", entity_type) \
            .eq("entity_id", str(entity_id)) \
            .order("created_at", desc=True) \
            .limit(limit).execute()
        return result.data or []
```

### Analytics Aggregation (`backend/signals/analytics.py`)

```python
from uuid import UUID
from datetime import datetime, timedelta
from collections import Counter
from backend.contracts.shared import SignalType
from supabase import Client


class AnalyticsService:
    """Aggregate analytics queries powered by the signal layer."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def get_funnel_data(
        self,
        days: int = 30,
    ) -> dict:
        """
        Compute the recruitment funnel:
        Ingested → Matched → Shortlisted → Intro Requested → Placed

        Returns counts at each stage and drop-off percentages.
        """
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        # Query signal counts for each funnel stage
        stages = {
            "ingested": SignalType.candidate_ingested.value,
            "matched": SignalType.match_generated.value,
            "shortlisted": SignalType.candidate_shortlisted.value,
            "intro_requested": SignalType.intro_requested.value,
            "placed": SignalType.placement_made.value,
        }

        funnel = {}
        for stage_name, event_type in stages.items():
            result = self.supabase.table("signals").select("id", count="exact") \
                .eq("event_type", event_type) \
                .gte("created_at", since).execute()
            funnel[stage_name] = result.count or 0

        # Compute drop-off rates
        stage_order = ["ingested", "matched", "shortlisted", "intro_requested", "placed"]
        dropoff = {}
        for i in range(1, len(stage_order)):
            prev = funnel[stage_order[i - 1]]
            curr = funnel[stage_order[i]]
            if prev > 0:
                dropoff[f"{stage_order[i-1]}_to_{stage_order[i]}"] = round(curr / prev * 100, 1)
            else:
                dropoff[f"{stage_order[i-1]}_to_{stage_order[i]}"] = 0.0

        return {
            "period_days": days,
            "stages": funnel,
            "conversion_rates": dropoff,
        }

    async def get_trending_skills(
        self,
        days: int = 30,
        top_k: int = 20,
    ) -> list[dict]:
        """
        Get most in-demand skills across all active roles.
        Extracted from role required_skills fields.
        """
        result = self.supabase.table("roles").select("required_skills, preferred_skills") \
            .eq("status", "active").execute()

        skill_counts = Counter()
        for role in (result.data or []):
            for skill in (role.get("required_skills") or []):
                if isinstance(skill, dict):
                    skill_counts[skill.get("name", "")] += 2  # required = 2x weight
            for skill in (role.get("preferred_skills") or []):
                if isinstance(skill, dict):
                    skill_counts[skill.get("name", "")] += 1

        trending = [
            {"skill": name, "demand_score": count}
            for name, count in skill_counts.most_common(top_k)
            if name  # filter empty
        ]

        return trending

    async def get_partner_performance(
        self,
        days: int = 30,
    ) -> list[dict]:
        """
        Partner performance metrics:
        - Candidates added
        - Handoffs sent/received/accepted
        - Placement conversion rate
        - Average handoff response time
        """
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        # Get all partner signals
        result = self.supabase.table("signals").select("*") \
            .eq("actor_role", "talent_partner") \
            .gte("created_at", since).execute()

        signals = result.data or []

        # Group by actor
        partner_stats: dict[str, dict] = {}
        for s in signals:
            pid = s["actor_id"]
            if pid not in partner_stats:
                partner_stats[pid] = {
                    "partner_id": pid,
                    "candidates_added": 0,
                    "handoffs_sent": 0,
                    "handoffs_received": 0,
                    "handoffs_accepted": 0,
                    "placements": 0,
                }

            event = s["event_type"]
            if event == SignalType.candidate_ingested.value:
                partner_stats[pid]["candidates_added"] += 1
            elif event == SignalType.handoff_sent.value:
                partner_stats[pid]["handoffs_sent"] += 1
            elif event == SignalType.handoff_accepted.value:
                partner_stats[pid]["handoffs_accepted"] += 1
            elif event == SignalType.placement_made.value:
                partner_stats[pid]["placements"] += 1

        # Also count handoffs received (where partner is the to_partner)
        handoffs_received = self.supabase.table("signals").select("*") \
            .eq("event_type", SignalType.handoff_sent.value) \
            .gte("created_at", since).execute()
        for s in (handoffs_received.data or []):
            to_id = (s.get("metadata") or {}).get("to_partner_id")
            if to_id and to_id in partner_stats:
                partner_stats[to_id]["handoffs_received"] += 1

        return list(partner_stats.values())

    async def get_client_engagement(
        self,
        days: int = 30,
    ) -> list[dict]:
        """
        Client engagement metrics:
        - Roles posted
        - Candidates viewed
        - Shortlist rate
        - Quote acceptance rate
        """
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        result = self.supabase.table("signals").select("*") \
            .eq("actor_role", "client") \
            .gte("created_at", since).execute()

        signals = result.data or []

        client_stats: dict[str, dict] = {}
        for s in signals:
            cid = s["actor_id"]
            if cid not in client_stats:
                client_stats[cid] = {
                    "client_id": cid,
                    "candidates_viewed": 0,
                    "candidates_shortlisted": 0,
                    "candidates_dismissed": 0,
                    "intros_requested": 0,
                    "quotes_accepted": 0,
                }

            event = s["event_type"]
            if event == SignalType.candidate_viewed.value:
                client_stats[cid]["candidates_viewed"] += 1
            elif event == SignalType.candidate_shortlisted.value:
                client_stats[cid]["candidates_shortlisted"] += 1
            elif event == SignalType.candidate_dismissed.value:
                client_stats[cid]["candidates_dismissed"] += 1
            elif event == SignalType.intro_requested.value:
                client_stats[cid]["intros_requested"] += 1

        # Compute shortlist rate
        for stats in client_stats.values():
            total_reviewed = stats["candidates_shortlisted"] + stats["candidates_dismissed"]
            if total_reviewed > 0:
                stats["shortlist_rate"] = round(
                    stats["candidates_shortlisted"] / total_reviewed * 100, 1
                )
            else:
                stats["shortlist_rate"] = 0.0

        return list(client_stats.values())

    async def get_time_series(
        self,
        event_type: str | None = None,
        days: int = 30,
        granularity: str = "day",  # day | week
    ) -> list[dict]:
        """
        Time-series data for charting. Returns counts per time bucket.
        Supports day and week granularity.
        """
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        query = self.supabase.table("signals").select("created_at, event_type") \
            .gte("created_at", since) \
            .order("created_at", desc=False)

        if event_type:
            query = query.eq("event_type", event_type)

        result = query.execute()
        signals = result.data or []

        # Bucket by date
        buckets: dict[str, int] = {}
        for s in signals:
            dt = datetime.fromisoformat(s["created_at"].replace("Z", "+00:00"))
            if granularity == "week":
                # ISO week start (Monday)
                week_start = dt - timedelta(days=dt.weekday())
                key = week_start.strftime("%Y-%m-%d")
            else:
                key = dt.strftime("%Y-%m-%d")

            buckets[key] = buckets.get(key, 0) + 1

        # Fill in missing dates
        start_date = datetime.utcnow() - timedelta(days=days)
        series = []
        current = start_date
        while current <= datetime.utcnow():
            key = current.strftime("%Y-%m-%d")
            series.append({
                "date": key,
                "count": buckets.get(key, 0),
            })
            if granularity == "week":
                current += timedelta(days=7)
            else:
                current += timedelta(days=1)

        return series
```

### Signal + Analytics Endpoints (`backend/api/signals.py`)

```python
from fastapi import APIRouter, Depends, Query
from uuid import UUID
from datetime import datetime
from typing import Optional
from backend.api.auth import get_current_user, require_role
from backend.contracts.shared import UserRole, SignalType
from backend.signals.tracker import SignalTracker
from backend.signals.analytics import AnalyticsService
from supabase import Client

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("/recent")
async def get_recent_signals(
    limit: int = Query(default=50, le=200),
    event_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    since: Optional[datetime] = None,
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """
    Get recent signals. Talent partners see their own signals.
    Admins see all signals. Used for activity feeds.
    """
    tracker = SignalTracker(supabase)

    # Non-admins only see their own signals
    actor_id = None if user["role"] == "admin" else UUID(user["id"])

    return await tracker.get_recent(
        limit=limit,
        event_type=event_type,
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=entity_id,
        since=since,
    )


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_signals(
    entity_type: str,
    entity_id: UUID,
    limit: int = Query(default=100, le=500),
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """Get all signals for a specific entity (candidate, role, match, etc.)."""
    tracker = SignalTracker(supabase)
    return await tracker.get_signals_for_entity(entity_type, entity_id, limit)


@router.get("/analytics/funnel")
async def get_funnel(
    days: int = Query(default=30, le=365),
    user=Depends(require_role([UserRole.talent_partner, UserRole.admin])),
    supabase: Client = Depends(),
):
    """Get recruitment funnel data: ingested → matched → shortlisted → placed."""
    analytics = AnalyticsService(supabase)
    return await analytics.get_funnel_data(days=days)


@router.get("/analytics/trending-skills")
async def get_trending_skills(
    days: int = Query(default=30, le=365),
    top_k: int = Query(default=20, le=50),
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """Get most in-demand skills across active roles."""
    analytics = AnalyticsService(supabase)
    return await analytics.get_trending_skills(days=days, top_k=top_k)


@router.get("/analytics/partner-performance")
async def get_partner_performance(
    days: int = Query(default=30, le=365),
    user=Depends(require_role([UserRole.admin])),
    supabase: Client = Depends(),
):
    """Get performance metrics for all talent partners. Admin only."""
    analytics = AnalyticsService(supabase)
    return await analytics.get_partner_performance(days=days)


@router.get("/analytics/client-engagement")
async def get_client_engagement(
    days: int = Query(default=30, le=365),
    user=Depends(require_role([UserRole.admin])),
    supabase: Client = Depends(),
):
    """Get engagement metrics for all clients. Admin only."""
    analytics = AnalyticsService(supabase)
    return await analytics.get_client_engagement(days=days)


@router.get("/analytics/time-series")
async def get_time_series(
    event_type: Optional[str] = None,
    days: int = Query(default=30, le=365),
    granularity: str = Query(default="day", regex="^(day|week)$"),
    user=Depends(require_role([UserRole.talent_partner, UserRole.admin])),
    supabase: Client = Depends(),
):
    """Get time-series data for charting. Supports day and week granularity."""
    analytics = AnalyticsService(supabase)
    return await analytics.get_time_series(
        event_type=event_type, days=days, granularity=granularity
    )
```

### Tests (`backend/tests/test_signals.py`)

```python
import pytest
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4
from datetime import datetime
from backend.signals.tracker import SignalTracker
from backend.signals.analytics import AnalyticsService
from backend.contracts.shared import SignalType, UserRole


@pytest.fixture
def mock_supabase():
    mock = MagicMock()
    # Default: insert returns the record
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
async def test_emit_signal_string_types(tracker, mock_supabase):
    """Signal tracker accepts both enum and string types."""
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
            "event_type": SignalType.candidate_ingested,
            "actor_id": uuid4(),
            "actor_role": UserRole.talent_partner,
            "entity_type": "candidate",
            "entity_id": uuid4(),
        },
        {
            "event_type": SignalType.match_generated,
            "actor_id": uuid4(),
            "actor_role": UserRole.talent_partner,
            "entity_type": "match",
            "entity_id": uuid4(),
        },
    ]
    count = await tracker.emit_batch(signals)
    assert count == 2


def test_signal_type_enum_values():
    """Verify all expected signal types exist."""
    expected = [
        "candidate_ingested", "candidate_viewed", "candidate_shortlisted",
        "candidate_dismissed", "match_generated", "intro_requested",
        "handoff_sent", "handoff_accepted", "handoff_declined",
        "quote_generated", "placement_made", "copilot_query",
    ]
    for event in expected:
        assert hasattr(SignalType, event)


def test_funnel_stages_ordered():
    """Funnel stages must follow the correct recruitment pipeline order."""
    stages = ["ingested", "matched", "shortlisted", "intro_requested", "placed"]
    assert stages[0] == "ingested"
    assert stages[-1] == "placed"
```

## Outputs
- `backend/signals/__init__.py`
- `backend/signals/tracker.py`
- `backend/signals/analytics.py`
- `backend/api/signals.py`
- `backend/tests/test_signals.py`

## Acceptance Criteria
1. `SignalTracker.emit()` stores a signal event in the `signals` table
2. `SignalTracker.emit_batch()` stores multiple signals efficiently
3. `GET /api/signals/recent` returns recent signals with optional filters
4. `GET /api/signals/analytics/funnel` returns correct funnel stage counts and conversion rates
5. `GET /api/signals/analytics/trending-skills` returns top skills by demand
6. `GET /api/signals/analytics/partner-performance` returns per-partner metrics (admin only)
7. `GET /api/signals/analytics/client-engagement` returns per-client metrics (admin only)
8. `GET /api/signals/analytics/time-series` returns bucketed counts by day or week
9. Non-admin users only see their own signals in the recent endpoint
10. All tests pass: `python -m pytest tests/test_signals.py -v`

## Handoff Notes
- **To Task 11:** The `SignalTracker` is ready to be imported and used from match/collection endpoints. Call `tracker.emit()` on every status change, shortlist, dismiss, etc.
- **To Task 13:** Handoff and quote actions should emit signals. Import and call `SignalTracker.emit()` with the appropriate `SignalType`.
- **To Task 15:** Admin endpoints will use `AnalyticsService` for platform stats. The funnel, trending skills, and performance methods are ready.
- **To Agent B:** Activity feed component should poll `GET /api/signals/recent`. Analytics charts should use the `/analytics/*` endpoints. Time-series endpoint supports `granularity=day|week` for chart x-axis. Funnel data includes `conversion_rates` for drop-off visualization.
- **Decision:** Analytics are computed on-the-fly from signals (not pre-aggregated). For the PoC scale this is fast enough. Production would add materialized views or a time-series database.
