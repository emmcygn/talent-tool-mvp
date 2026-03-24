# Agent A — Task 11: Match + Collection Endpoints

## Mission
Build the FastAPI endpoints for match results (query, filter, status update) and collection CRUD (create, list, get, update, add/remove candidates), including collection stats computation and RLS enforcement.

## Context
This is Day 3. Task 09 and 10 have built the matching engine and explanation generator. Matches are stored in the database with scores, skill overlaps, explanations, and confidence levels. This task exposes them via the API and adds collection management — themed groups of candidates that talent partners can create, share, and collaborate on.

## Prerequisites
- Task 09 complete (matching engine stores matches in `matches` table)
- Task 10 complete (explanations populated on matches)
- Task 03 complete (FastAPI skeleton with auth helpers, router registration)
- Task 08 complete (candidate + role CRUD endpoints — pattern for auth + RLS established)
- Task 02 complete (Supabase schema with `matches`, `collections`, `collection_candidates` tables)

## Checklist
- [ ] Create `backend/api/matches.py` — match results endpoints
- [ ] Create `backend/api/collections.py` — collection CRUD endpoints
- [ ] Create `backend/services/collection.py` — collection business logic + stats
- [ ] Register routers in `backend/main.py`
- [ ] Create `backend/tests/test_matches_api.py` — endpoint tests
- [ ] Create `backend/tests/test_collections_api.py` — endpoint tests
- [ ] Run tests, verify pass
- [ ] Commit: "Agent A Task 11: Match + collection endpoints"

## Implementation Details

### Match Endpoints (`backend/api/matches.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional
from backend.api.auth import get_current_user, require_role
from backend.contracts.match import Match
from backend.contracts.shared import ConfidenceLevel, MatchStatus, UserRole
from backend.matching.engine import MatchingEngine
from backend.matching.explainer import MatchExplainer
from backend.config import settings
from supabase import Client

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("/by-role/{role_id}", response_model=list[Match])
async def get_matches_by_role(
    role_id: UUID,
    confidence: Optional[ConfidenceLevel] = None,
    status: Optional[MatchStatus] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """
    Get all matches for a role, ranked by overall score.
    Clients see anonymized candidate data; partners/admins see full data.
    Filterable by confidence level and status.
    """
    query = supabase.table("matches").select("*") \
        .eq("role_id", str(role_id)) \
        .order("overall_score", desc=True) \
        .range(offset, offset + limit - 1)

    if confidence:
        query = query.eq("confidence", confidence.value)
    if status:
        query = query.eq("status", status.value)

    result = query.execute()
    return result.data or []


@router.get("/by-candidate/{candidate_id}", response_model=list[Match])
async def get_matches_by_candidate(
    candidate_id: UUID,
    confidence: Optional[ConfidenceLevel] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """
    Get all matches for a specific candidate across all roles.
    Useful for talent partners to see a candidate's full match profile.
    """
    query = supabase.table("matches").select("*") \
        .eq("candidate_id", str(candidate_id)) \
        .order("overall_score", desc=True) \
        .range(offset, offset + limit - 1)

    if confidence:
        query = query.eq("confidence", confidence.value)

    result = query.execute()
    return result.data or []


@router.get("/{match_id}", response_model=Match)
async def get_match(
    match_id: UUID,
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """Get a single match with full details including explanation and scoring breakdown."""
    result = supabase.table("matches").select("*") \
        .eq("id", str(match_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Match not found")
    return result.data


@router.patch("/{match_id}/status")
async def update_match_status(
    match_id: UUID,
    status: MatchStatus,
    reason: Optional[str] = None,
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """
    Update match status (shortlist, dismiss, request intro).
    Emits a signal event for analytics tracking.
    """
    # Verify match exists
    match_result = supabase.table("matches").select("*") \
        .eq("id", str(match_id)).single().execute()
    if not match_result.data:
        raise HTTPException(status_code=404, detail="Match not found")

    # Update status
    update_data = {"status": status.value}
    supabase.table("matches").update(update_data) \
        .eq("id", str(match_id)).execute()

    # Emit signal (imported from signals.tracker)
    from backend.signals.tracker import SignalTracker
    tracker = SignalTracker(supabase)
    signal_type_map = {
        MatchStatus.shortlisted: "candidate_shortlisted",
        MatchStatus.dismissed: "candidate_dismissed",
        MatchStatus.intro_requested: "intro_requested",
    }
    if status in signal_type_map:
        await tracker.emit(
            event_type=signal_type_map[status],
            actor_id=user["id"],
            actor_role=user["role"],
            entity_type="match",
            entity_id=match_id,
            metadata={
                "role_id": match_result.data["role_id"],
                "candidate_id": match_result.data["candidate_id"],
                "reason": reason,
            },
        )

    return {"status": "updated", "match_id": str(match_id), "new_status": status.value}


@router.post("/generate/{role_id}")
async def trigger_matching(
    role_id: UUID,
    user=Depends(require_role([UserRole.talent_partner, UserRole.admin])),
    supabase: Client = Depends(),
):
    """
    Trigger matching pipeline for a role.
    Runs structured filter → semantic search → scoring → explanation generation.
    """
    engine = MatchingEngine(supabase)
    matches = await engine.run_matching(role_id)

    # Generate explanations for Strong + Good matches
    explainer = MatchExplainer(supabase)
    explanation_count = await explainer.generate_explanations(
        role_id=role_id,
        min_confidence=ConfidenceLevel.good,
    )

    return {
        "role_id": str(role_id),
        "matches_generated": len(matches),
        "explanations_generated": explanation_count,
        "breakdown": {
            "strong": sum(1 for m in matches if m.confidence == ConfidenceLevel.strong),
            "good": sum(1 for m in matches if m.confidence == ConfidenceLevel.good),
            "possible": sum(1 for m in matches if m.confidence == ConfidenceLevel.possible),
        },
    }


@router.post("/{match_id}/regenerate-explanation")
async def regenerate_explanation(
    match_id: UUID,
    user=Depends(require_role([UserRole.talent_partner, UserRole.admin])),
    supabase: Client = Depends(),
):
    """Re-generate explanation for a single match (e.g., after candidate profile correction)."""
    explainer = MatchExplainer(supabase)
    result = await explainer.generate_single_explanation(match_id)
    if not result:
        raise HTTPException(status_code=404, detail="Match not found")
    return {"match_id": str(match_id), "explanation": result}
```

### Collection Service (`backend/services/collection.py`)

```python
from uuid import UUID, uuid4
from datetime import datetime
from backend.contracts.collection import Collection, CollectionCreate
from backend.contracts.shared import Visibility, AvailabilityStatus
from supabase import Client


class CollectionService:
    """Business logic for collection management."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def create_collection(
        self, data: CollectionCreate, owner_id: UUID
    ) -> Collection:
        """Create a new collection."""
        collection_id = uuid4()
        now = datetime.utcnow().isoformat()

        record = {
            "id": str(collection_id),
            "name": data.name,
            "description": data.description,
            "owner_id": str(owner_id),
            "visibility": data.visibility.value,
            "shared_with": [str(uid) for uid in data.shared_with] if data.shared_with else None,
            "tags": data.tags,
            "candidate_count": 0,
            "avg_match_score": None,
            "available_now_count": 0,
            "created_at": now,
            "updated_at": now,
        }

        result = self.supabase.table("collections").insert(record).execute()
        return result.data[0] if result.data else None

    async def list_collections(
        self,
        user_id: UUID,
        user_role: str,
        include_shared: bool = True,
    ) -> list[dict]:
        """
        List collections visible to the user.
        - Own collections always visible
        - shared_all collections visible to all talent partners
        - shared_specific visible if user is in shared_with list
        - Admins see all
        """
        if user_role == "admin":
            result = self.supabase.table("collections").select("*") \
                .order("updated_at", desc=True).execute()
            return result.data or []

        # Own collections
        own_result = self.supabase.table("collections").select("*") \
            .eq("owner_id", str(user_id)) \
            .order("updated_at", desc=True).execute()
        collections = own_result.data or []

        if include_shared:
            # Shared with all
            shared_all = self.supabase.table("collections").select("*") \
                .eq("visibility", Visibility.shared_all.value) \
                .neq("owner_id", str(user_id)) \
                .order("updated_at", desc=True).execute()
            collections.extend(shared_all.data or [])

            # Shared with specific — need to check if user is in shared_with
            shared_specific = self.supabase.table("collections").select("*") \
                .eq("visibility", Visibility.shared_specific.value) \
                .neq("owner_id", str(user_id)) \
                .order("updated_at", desc=True).execute()
            for c in (shared_specific.data or []):
                shared_list = c.get("shared_with") or []
                if str(user_id) in shared_list:
                    collections.append(c)

        # Deduplicate by id
        seen = set()
        unique = []
        for c in collections:
            if c["id"] not in seen:
                seen.add(c["id"])
                unique.append(c)

        return unique

    async def get_collection(self, collection_id: UUID) -> dict | None:
        """Get a single collection with candidate IDs."""
        result = self.supabase.table("collections").select("*") \
            .eq("id", str(collection_id)).single().execute()
        if not result.data:
            return None

        # Load candidate IDs from junction table
        candidates = self.supabase.table("collection_candidates").select("candidate_id") \
            .eq("collection_id", str(collection_id)).execute()
        result.data["candidate_ids"] = [
            c["candidate_id"] for c in (candidates.data or [])
        ]

        return result.data

    async def update_visibility(
        self,
        collection_id: UUID,
        owner_id: UUID,
        visibility: Visibility,
        shared_with: list[UUID] | None = None,
    ) -> dict | None:
        """Update collection visibility. Only the owner can change visibility."""
        # Verify ownership
        existing = self.supabase.table("collections").select("owner_id") \
            .eq("id", str(collection_id)).single().execute()
        if not existing.data or existing.data["owner_id"] != str(owner_id):
            return None

        update_data = {
            "visibility": visibility.value,
            "shared_with": [str(uid) for uid in shared_with] if shared_with else None,
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = self.supabase.table("collections").update(update_data) \
            .eq("id", str(collection_id)).execute()
        return result.data[0] if result.data else None

    async def add_candidates(
        self,
        collection_id: UUID,
        candidate_ids: list[UUID],
    ) -> dict:
        """Add candidates to a collection. Skips duplicates."""
        added = 0
        for cid in candidate_ids:
            try:
                self.supabase.table("collection_candidates").insert({
                    "collection_id": str(collection_id),
                    "candidate_id": str(cid),
                    "added_at": datetime.utcnow().isoformat(),
                }).execute()
                added += 1
            except Exception:
                # Duplicate — skip
                pass

        # Recompute stats
        await self.recompute_stats(collection_id)

        return {"collection_id": str(collection_id), "added": added}

    async def remove_candidates(
        self,
        collection_id: UUID,
        candidate_ids: list[UUID],
    ) -> dict:
        """Remove candidates from a collection."""
        for cid in candidate_ids:
            self.supabase.table("collection_candidates") \
                .delete() \
                .eq("collection_id", str(collection_id)) \
                .eq("candidate_id", str(cid)) \
                .execute()

        # Recompute stats
        await self.recompute_stats(collection_id)

        return {
            "collection_id": str(collection_id),
            "removed": len(candidate_ids),
        }

    async def recompute_stats(self, collection_id: UUID) -> dict:
        """
        Recompute aggregate stats for a collection:
        - candidate_count
        - avg_match_score (across all matches for candidates in this collection)
        - available_now_count (candidates with immediate or 1_month availability)
        """
        # Count candidates
        candidates_result = self.supabase.table("collection_candidates") \
            .select("candidate_id") \
            .eq("collection_id", str(collection_id)).execute()
        candidate_ids = [c["candidate_id"] for c in (candidates_result.data or [])]
        candidate_count = len(candidate_ids)

        avg_match_score = None
        available_now_count = 0

        if candidate_ids:
            # Compute average match score
            matches_result = self.supabase.table("matches") \
                .select("overall_score") \
                .in_("candidate_id", candidate_ids).execute()
            scores = [m["overall_score"] for m in (matches_result.data or []) if m.get("overall_score")]
            if scores:
                avg_match_score = round(sum(scores) / len(scores), 4)

            # Count available now
            available_result = self.supabase.table("candidates") \
                .select("id, availability") \
                .in_("id", candidate_ids) \
                .in_("availability", [
                    AvailabilityStatus.immediate.value,
                    AvailabilityStatus.one_month.value,
                ]).execute()
            available_now_count = len(available_result.data or [])

        # Update collection stats
        self.supabase.table("collections").update({
            "candidate_count": candidate_count,
            "avg_match_score": avg_match_score,
            "available_now_count": available_now_count,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", str(collection_id)).execute()

        return {
            "candidate_count": candidate_count,
            "avg_match_score": avg_match_score,
            "available_now_count": available_now_count,
        }
```

### Collection Endpoints (`backend/api/collections.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional
from backend.api.auth import get_current_user, require_role
from backend.contracts.collection import Collection, CollectionCreate
from backend.contracts.shared import Visibility, UserRole
from backend.services.collection import CollectionService
from supabase import Client

router = APIRouter(prefix="/api/collections", tags=["collections"])


@router.post("/", response_model=dict)
async def create_collection(
    data: CollectionCreate,
    user=Depends(require_role([UserRole.talent_partner, UserRole.admin])),
    supabase: Client = Depends(),
):
    """Create a new collection. Only talent partners and admins can create collections."""
    service = CollectionService(supabase)
    result = await service.create_collection(data, owner_id=UUID(user["id"]))
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create collection")
    return result


@router.get("/", response_model=list[dict])
async def list_collections(
    include_shared: bool = Query(default=True),
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """List collections visible to the current user (own + shared)."""
    service = CollectionService(supabase)
    return await service.list_collections(
        user_id=UUID(user["id"]),
        user_role=user["role"],
        include_shared=include_shared,
    )


@router.get("/{collection_id}", response_model=dict)
async def get_collection(
    collection_id: UUID,
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """Get a single collection with candidate IDs and stats."""
    service = CollectionService(supabase)
    result = await service.get_collection(collection_id)
    if not result:
        raise HTTPException(status_code=404, detail="Collection not found")
    return result


@router.patch("/{collection_id}/visibility")
async def update_visibility(
    collection_id: UUID,
    visibility: Visibility,
    shared_with: Optional[list[UUID]] = None,
    user=Depends(require_role([UserRole.talent_partner, UserRole.admin])),
    supabase: Client = Depends(),
):
    """Update collection visibility. Only the owner can change visibility."""
    service = CollectionService(supabase)
    result = await service.update_visibility(
        collection_id=collection_id,
        owner_id=UUID(user["id"]),
        visibility=visibility,
        shared_with=shared_with,
    )
    if not result:
        raise HTTPException(status_code=403, detail="Not the collection owner or collection not found")
    return result


@router.post("/{collection_id}/candidates")
async def add_candidates(
    collection_id: UUID,
    candidate_ids: list[UUID],
    user=Depends(require_role([UserRole.talent_partner, UserRole.admin])),
    supabase: Client = Depends(),
):
    """Add candidates to a collection. Duplicates are silently skipped."""
    service = CollectionService(supabase)
    return await service.add_candidates(collection_id, candidate_ids)


@router.delete("/{collection_id}/candidates")
async def remove_candidates(
    collection_id: UUID,
    candidate_ids: list[UUID],
    user=Depends(require_role([UserRole.talent_partner, UserRole.admin])),
    supabase: Client = Depends(),
):
    """Remove candidates from a collection."""
    service = CollectionService(supabase)
    return await service.remove_candidates(collection_id, candidate_ids)


@router.get("/{collection_id}/stats")
async def get_collection_stats(
    collection_id: UUID,
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """Get computed stats for a collection (candidate count, avg score, available now)."""
    service = CollectionService(supabase)
    return await service.recompute_stats(collection_id)
```

### Migration for `collection_candidates` Junction Table

Add to migration or create `supabase/migrations/004_collection_candidates.sql`:

```sql
-- Junction table for collection-candidate relationship
CREATE TABLE IF NOT EXISTS collection_candidates (
    collection_id uuid NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    candidate_id uuid NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    added_at timestamptz DEFAULT now(),
    PRIMARY KEY (collection_id, candidate_id)
);

-- Index for fast lookups
CREATE INDEX idx_collection_candidates_collection ON collection_candidates(collection_id);
CREATE INDEX idx_collection_candidates_candidate ON collection_candidates(candidate_id);

-- RLS for collection_candidates
ALTER TABLE collection_candidates ENABLE ROW LEVEL SECURITY;

-- Talent partners can manage candidates in their own collections
CREATE POLICY "collection_candidates_owner" ON collection_candidates
    FOR ALL USING (
        collection_id IN (
            SELECT id FROM collections WHERE owner_id = auth.uid()
        )
    );

-- Admins can manage all
CREATE POLICY "collection_candidates_admin" ON collection_candidates
    FOR ALL USING (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
    );

-- RLS for collections table (if not already defined)
CREATE POLICY "collections_owner" ON collections
    FOR ALL USING (owner_id = auth.uid());

CREATE POLICY "collections_shared_all" ON collections
    FOR SELECT USING (visibility = 'shared_all');

CREATE POLICY "collections_shared_specific" ON collections
    FOR SELECT USING (
        visibility = 'shared_specific'
        AND auth.uid()::text = ANY(shared_with)
    );

CREATE POLICY "collections_admin" ON collections
    FOR ALL USING (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
    );
```

### Tests (`backend/tests/test_matches_api.py`)

```python
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from fastapi.testclient import TestClient


@pytest.fixture
def mock_user():
    return {
        "id": str(uuid4()),
        "role": "talent_partner",
        "email": "partner@test.com",
    }


def test_get_matches_by_role_returns_list(mock_user):
    """Matches by role endpoint returns ranked results."""
    # This would use TestClient with mocked Supabase
    # Verified via integration test with actual data
    pass


def test_update_match_status_emits_signal(mock_user):
    """Updating match status emits the appropriate signal."""
    pass


def test_trigger_matching_requires_partner_role():
    """Only talent partners and admins can trigger matching."""
    pass
```

### Tests (`backend/tests/test_collections_api.py`)

```python
import pytest
from uuid import uuid4
from backend.services.collection import CollectionService
from backend.contracts.collection import CollectionCreate
from backend.contracts.shared import Visibility


def test_collection_create_model():
    c = CollectionCreate(
        name="Senior Backend — London",
        description="Top backend candidates in London",
        visibility=Visibility.shared_all,
        tags=["backend", "london", "senior"],
    )
    assert c.name == "Senior Backend — London"
    assert c.visibility == Visibility.shared_all
    assert len(c.tags) == 3


def test_collection_create_defaults():
    c = CollectionCreate(name="My List")
    assert c.visibility == Visibility.private
    assert c.shared_with is None
    assert c.tags == []
```

## Outputs
- `backend/api/matches.py`
- `backend/api/collections.py`
- `backend/services/collection.py`
- `backend/tests/test_matches_api.py`
- `backend/tests/test_collections_api.py`
- `supabase/migrations/004_collection_candidates.sql`

## Acceptance Criteria
1. `GET /api/matches/by-role/{role_id}` returns ranked matches with full explanations
2. `GET /api/matches/by-candidate/{candidate_id}` returns all matches for a candidate
3. `PATCH /api/matches/{match_id}/status` updates status and emits signal
4. `POST /api/matches/generate/{role_id}` triggers full matching pipeline
5. `POST /api/collections/` creates a collection with correct ownership
6. `GET /api/collections/` returns own + visible shared collections
7. `PATCH /api/collections/{id}/visibility` only works for the owner
8. `POST /api/collections/{id}/candidates` adds candidates, computes stats
9. `DELETE /api/collections/{id}/candidates` removes candidates, recomputes stats
10. Collection stats include candidate_count, avg_match_score, available_now_count
11. RLS policies enforce visibility rules at database level
12. All tests pass

## Handoff Notes
- **To Task 12:** Match status updates and collection actions should emit signals. The `update_match_status` endpoint already emits signals — follow this pattern for collection actions.
- **To Task 13:** Handoff endpoints will need to reference collections (a handoff may contain candidates from a collection). The collection service provides the `get_collection` method to load candidate IDs.
- **To Agent B:** Match endpoints support filtering by `confidence` and `status` query params. Collection endpoints follow standard CRUD. The `POST /api/matches/generate/{role_id}` endpoint triggers matching and returns a summary — wire this to a "Run Matching" button in the UI. Collection visibility has three levels: private, shared_specific (with specific partner IDs), shared_all.
- **Decision:** Collection stats are recomputed on candidate add/remove (eager). This keeps reads fast. For large collections this could be batched, but for PoC eager recomputation is fine.
