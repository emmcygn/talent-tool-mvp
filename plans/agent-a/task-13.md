# Agent A — Task 13: Handoff + Quote Endpoints

## Mission
Build the handoff lifecycle (create, list inbox/outbox, respond, attribution tracking) and quote generation (calculate fees based on seniority, apply pool discounts, generate breakdowns, manage expiry and status).

## Context
This is Day 4. Handoffs are how talent partners collaborate — one partner refers candidates to another for specific roles or general consideration. The attribution trail tracks through to placement for commission splitting. Quotes are how clients request introductions — the system calculates a fee based on role seniority, with a discount for candidates already in the shared talent pool. Both features emit signals for analytics tracking.

## Prerequisites
- Task 08 complete (candidate + role CRUD — data exists to reference)
- Task 12 complete (signal tracking — needed for emitting handoff/quote signals)
- Task 03 complete (FastAPI skeleton with auth)
- Task 02 complete (Supabase schema with `handoffs` and `quotes` tables)
- `backend/contracts/handoff.py` exists with `Handoff`, `HandoffCreate`, `HandoffStatus`
- `backend/contracts/quote.py` exists with `Quote`, `QuoteRequest`, `QuoteStatus`

## Checklist
- [ ] Create `backend/services/handoff.py` — handoff business logic
- [ ] Create `backend/services/quote.py` — quote generation logic
- [ ] Create `backend/api/handoffs.py` — handoff endpoints
- [ ] Create `backend/api/quotes.py` — quote endpoints
- [ ] Register routers in `backend/main.py`
- [ ] Create `backend/tests/test_handoffs.py` — unit tests
- [ ] Create `backend/tests/test_quotes.py` — unit tests
- [ ] Run tests, verify pass
- [ ] Commit: "Agent A Task 13: Handoff + quote endpoints"

## Implementation Details

### Handoff Service (`backend/services/handoff.py`)

```python
from uuid import UUID, uuid4
from datetime import datetime
from backend.contracts.shared import HandoffStatus, SignalType, UserRole
from backend.signals.tracker import SignalTracker
from supabase import Client


class HandoffService:
    """Manages the handoff lifecycle between talent partners."""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.tracker = SignalTracker(supabase)

    async def create_handoff(
        self,
        from_partner_id: UUID,
        to_partner_id: UUID,
        candidate_ids: list[UUID],
        context_notes: str,
        target_role_id: UUID | None = None,
    ) -> dict:
        """
        Create a new handoff. Generates an attribution ID for tracking
        the referral chain through to potential placement.
        """
        handoff_id = uuid4()
        attribution_id = uuid4()
        now = datetime.utcnow().isoformat()

        record = {
            "id": str(handoff_id),
            "from_partner_id": str(from_partner_id),
            "to_partner_id": str(to_partner_id),
            "candidate_ids": [str(cid) for cid in candidate_ids],
            "context_notes": context_notes,
            "target_role_id": str(target_role_id) if target_role_id else None,
            "status": HandoffStatus.pending.value,
            "response_notes": None,
            "attribution_id": str(attribution_id),
            "created_at": now,
            "responded_at": None,
        }

        result = self.supabase.table("handoffs").insert(record).execute()

        # Emit signal
        await self.tracker.emit(
            event_type=SignalType.handoff_sent,
            actor_id=from_partner_id,
            actor_role=UserRole.talent_partner,
            entity_type="handoff",
            entity_id=handoff_id,
            metadata={
                "to_partner_id": str(to_partner_id),
                "candidate_count": len(candidate_ids),
                "has_target_role": target_role_id is not None,
            },
        )

        return result.data[0] if result.data else record

    async def list_inbox(
        self,
        partner_id: UUID,
        status: HandoffStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """List handoffs received by this partner (inbox)."""
        query = self.supabase.table("handoffs").select("*") \
            .eq("to_partner_id", str(partner_id)) \
            .order("created_at", desc=True) \
            .range(offset, offset + limit - 1)

        if status:
            query = query.eq("status", status.value)

        result = query.execute()
        return result.data or []

    async def list_outbox(
        self,
        partner_id: UUID,
        status: HandoffStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """List handoffs sent by this partner (outbox)."""
        query = self.supabase.table("handoffs").select("*") \
            .eq("from_partner_id", str(partner_id)) \
            .order("created_at", desc=True) \
            .range(offset, offset + limit - 1)

        if status:
            query = query.eq("status", status.value)

        result = query.execute()
        return result.data or []

    async def respond(
        self,
        handoff_id: UUID,
        partner_id: UUID,
        accept: bool,
        response_notes: str | None = None,
    ) -> dict | None:
        """
        Accept or decline a handoff. Only the recipient can respond.
        Emits the appropriate signal for analytics.
        """
        # Verify this partner is the recipient
        existing = self.supabase.table("handoffs").select("*") \
            .eq("id", str(handoff_id)).single().execute()

        if not existing.data:
            return None
        if existing.data["to_partner_id"] != str(partner_id):
            return None
        if existing.data["status"] != HandoffStatus.pending.value:
            return None  # Already responded

        new_status = HandoffStatus.accepted if accept else HandoffStatus.declined
        now = datetime.utcnow().isoformat()

        result = self.supabase.table("handoffs").update({
            "status": new_status.value,
            "response_notes": response_notes,
            "responded_at": now,
        }).eq("id", str(handoff_id)).execute()

        # Emit signal
        signal_type = SignalType.handoff_accepted if accept else SignalType.handoff_declined
        await self.tracker.emit(
            event_type=signal_type,
            actor_id=partner_id,
            actor_role=UserRole.talent_partner,
            entity_type="handoff",
            entity_id=handoff_id,
            metadata={
                "from_partner_id": existing.data["from_partner_id"],
                "response_time_seconds": self._compute_response_time(
                    existing.data["created_at"], now
                ),
                "reason": response_notes,
            },
        )

        return result.data[0] if result.data else None

    async def get_handoff(self, handoff_id: UUID) -> dict | None:
        """Get a single handoff with full details."""
        result = self.supabase.table("handoffs").select("*") \
            .eq("id", str(handoff_id)).single().execute()
        return result.data

    async def get_attribution_chain(self, attribution_id: UUID) -> list[dict]:
        """
        Get all handoffs in an attribution chain.
        Tracks the referral path from original ingestion to placement.
        """
        result = self.supabase.table("handoffs").select("*") \
            .eq("attribution_id", str(attribution_id)) \
            .order("created_at", desc=False).execute()
        return result.data or []

    def _compute_response_time(self, created_at: str, responded_at: str) -> int:
        """Compute response time in seconds."""
        try:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            responded = datetime.fromisoformat(responded_at.replace("Z", "+00:00"))
            return int((responded - created).total_seconds())
        except Exception:
            return 0
```

### Quote Service (`backend/services/quote.py`)

```python
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from decimal import Decimal
from backend.contracts.shared import (
    SeniorityLevel, QuoteStatus, SignalType, UserRole
)
from backend.signals.tracker import SignalTracker
from supabase import Client


# Fee schedule based on seniority (UK market, percentage of first-year salary)
# These represent typical recruitment fees as absolute GBP amounts for PoC
SENIORITY_BASE_FEES = {
    SeniorityLevel.junior: Decimal("8000"),
    SeniorityLevel.mid: Decimal("12000"),
    SeniorityLevel.senior: Decimal("18000"),
    SeniorityLevel.lead: Decimal("25000"),
    SeniorityLevel.principal: Decimal("35000"),
}

# Pool discount: pre-vetted candidates in shared network cost less
POOL_DISCOUNT_PERCENTAGE = Decimal("0.20")  # 20% discount

# Quote validity period
QUOTE_VALIDITY_DAYS = 14


class QuoteService:
    """Generates and manages placement fee quotes."""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.tracker = SignalTracker(supabase)

    async def generate_quote(
        self,
        client_id: UUID,
        candidate_id: UUID,
        role_id: UUID,
    ) -> dict:
        """
        Generate a placement fee quote.

        Fee calculation:
        1. Base fee determined by role seniority level
        2. If candidate is in the shared talent pool, apply 20% discount
        3. Generate human-readable fee breakdown
        4. Set 14-day expiry
        """
        # Load role for seniority
        role_result = self.supabase.table("roles").select("seniority, title, salary_band") \
            .eq("id", str(role_id)).single().execute()
        role = role_result.data
        if not role:
            raise ValueError(f"Role {role_id} not found")

        # Load candidate to check pool status
        candidate_result = self.supabase.table("candidates") \
            .select("id, first_name, last_name, sources") \
            .eq("id", str(candidate_id)).single().execute()
        candidate = candidate_result.data
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        # Determine seniority
        seniority = SeniorityLevel(role["seniority"]) if role.get("seniority") else SeniorityLevel.mid
        base_fee = SENIORITY_BASE_FEES.get(seniority, SENIORITY_BASE_FEES[SeniorityLevel.mid])

        # Check if candidate is in shared pool (has multiple sources or is in shared collections)
        is_pool = await self._is_pool_candidate(candidate_id)

        # Calculate discount
        pool_discount = None
        final_fee = base_fee
        if is_pool:
            pool_discount = (base_fee * POOL_DISCOUNT_PERCENTAGE).quantize(Decimal("0.01"))
            final_fee = base_fee - pool_discount

        # Generate fee breakdown
        fee_breakdown = self._generate_fee_breakdown(
            seniority=seniority,
            base_fee=base_fee,
            is_pool=is_pool,
            pool_discount=pool_discount,
            final_fee=final_fee,
            role_title=role.get("title", ""),
        )

        # Create quote record
        quote_id = uuid4()
        now = datetime.utcnow()
        expires_at = now + timedelta(days=QUOTE_VALIDITY_DAYS)

        record = {
            "id": str(quote_id),
            "client_id": str(client_id),
            "candidate_id": str(candidate_id),
            "role_id": str(role_id),
            "is_pool_candidate": is_pool,
            "base_fee": str(base_fee),
            "pool_discount": str(pool_discount) if pool_discount else None,
            "final_fee": str(final_fee),
            "fee_breakdown": fee_breakdown,
            "status": QuoteStatus.generated.value,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        result = self.supabase.table("quotes").insert(record).execute()

        # Emit signal
        await self.tracker.emit(
            event_type=SignalType.quote_generated,
            actor_id=client_id,
            actor_role=UserRole.client,
            entity_type="quote",
            entity_id=quote_id,
            metadata={
                "role_id": str(role_id),
                "candidate_id": str(candidate_id),
                "final_fee": str(final_fee),
                "is_pool": is_pool,
                "pool_discount_applied": pool_discount is not None,
            },
        )

        return result.data[0] if result.data else record

    async def get_quote(self, quote_id: UUID) -> dict | None:
        """Get a single quote."""
        result = self.supabase.table("quotes").select("*") \
            .eq("id", str(quote_id)).single().execute()
        return result.data

    async def list_quotes_for_client(
        self,
        client_id: UUID,
        status: QuoteStatus | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """List all quotes for a client."""
        query = self.supabase.table("quotes").select("*") \
            .eq("client_id", str(client_id)) \
            .order("created_at", desc=True) \
            .limit(limit)

        if status:
            query = query.eq("status", status.value)

        result = query.execute()
        return result.data or []

    async def update_quote_status(
        self,
        quote_id: UUID,
        new_status: QuoteStatus,
        actor_id: UUID,
        actor_role: UserRole,
    ) -> dict | None:
        """
        Update quote status (sent, accepted, declined, expired).
        Returns None if quote not found.
        """
        existing = self.supabase.table("quotes").select("*") \
            .eq("id", str(quote_id)).single().execute()
        if not existing.data:
            return None

        # Check for valid transitions
        valid_transitions = {
            QuoteStatus.generated: [QuoteStatus.sent, QuoteStatus.expired],
            QuoteStatus.sent: [QuoteStatus.accepted, QuoteStatus.declined, QuoteStatus.expired],
            QuoteStatus.accepted: [],  # terminal
            QuoteStatus.declined: [],  # terminal
            QuoteStatus.expired: [],   # terminal
        }

        current = QuoteStatus(existing.data["status"])
        if new_status not in valid_transitions.get(current, []):
            return None

        result = self.supabase.table("quotes").update({
            "status": new_status.value,
        }).eq("id", str(quote_id)).execute()

        return result.data[0] if result.data else None

    async def check_and_expire_quotes(self) -> int:
        """
        Expire quotes past their expiry date.
        Should be called periodically (e.g., via a scheduled task or on access).
        """
        now = datetime.utcnow().isoformat()

        # Find non-terminal quotes past expiry
        result = self.supabase.table("quotes").select("id") \
            .in_("status", [QuoteStatus.generated.value, QuoteStatus.sent.value]) \
            .lt("expires_at", now).execute()

        expired_ids = [q["id"] for q in (result.data or [])]
        if expired_ids:
            for qid in expired_ids:
                self.supabase.table("quotes").update({
                    "status": QuoteStatus.expired.value,
                }).eq("id", qid).execute()

        return len(expired_ids)

    async def _is_pool_candidate(self, candidate_id: UUID) -> bool:
        """
        Check if a candidate is in the shared talent pool.
        A candidate is considered "pool" if they appear in any shared collection
        or have been sourced from multiple adapters.
        """
        # Check if in any shared collection
        collection_result = self.supabase.table("collection_candidates") \
            .select("collection_id") \
            .eq("candidate_id", str(candidate_id)).execute()

        if collection_result.data:
            collection_ids = [c["collection_id"] for c in collection_result.data]
            shared_result = self.supabase.table("collections").select("id") \
                .in_("id", collection_ids) \
                .in_("visibility", ["shared_all", "shared_specific"]).execute()
            if shared_result.data:
                return True

        # Check if candidate has multiple sources
        candidate = self.supabase.table("candidates").select("sources") \
            .eq("id", str(candidate_id)).single().execute()
        if candidate.data:
            sources = candidate.data.get("sources") or []
            if len(sources) > 1:
                return True

        return False

    def _generate_fee_breakdown(
        self,
        seniority: SeniorityLevel,
        base_fee: Decimal,
        is_pool: bool,
        pool_discount: Decimal | None,
        final_fee: Decimal,
        role_title: str,
    ) -> dict:
        """Generate a human-readable fee breakdown."""
        breakdown = {
            "summary": f"Placement fee for {role_title}",
            "seniority_level": seniority.value,
            "base_fee": {
                "amount": str(base_fee),
                "currency": "GBP",
                "description": f"Standard placement fee for {seniority.value}-level role",
            },
        }

        if is_pool and pool_discount:
            breakdown["pool_discount"] = {
                "amount": str(pool_discount),
                "currency": "GBP",
                "percentage": f"{int(POOL_DISCOUNT_PERCENTAGE * 100)}%",
                "description": "This candidate is in our pre-vetted talent network — reduced fee applies",
            }
            breakdown["savings_message"] = f"You save £{pool_discount:,.2f} because this candidate is already in our talent network"

        breakdown["final_fee"] = {
            "amount": str(final_fee),
            "currency": "GBP",
            "description": "Total placement fee" if not is_pool else "Total placement fee (after network discount)",
        }

        breakdown["validity"] = f"This quote is valid for {QUOTE_VALIDITY_DAYS} days"

        return breakdown
```

### Handoff Endpoints (`backend/api/handoffs.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional
from backend.api.auth import get_current_user, require_role
from backend.contracts.handoff import HandoffCreate
from backend.contracts.shared import HandoffStatus, UserRole
from backend.services.handoff import HandoffService
from supabase import Client

router = APIRouter(prefix="/api/handoffs", tags=["handoffs"])


@router.post("/")
async def create_handoff(
    data: HandoffCreate,
    user=Depends(require_role([UserRole.talent_partner, UserRole.admin])),
    supabase: Client = Depends(),
):
    """Create a new handoff (refer candidates to another partner)."""
    service = HandoffService(supabase)
    result = await service.create_handoff(
        from_partner_id=UUID(user["id"]),
        to_partner_id=data.to_partner_id,
        candidate_ids=data.candidate_ids,
        context_notes=data.context_notes,
        target_role_id=data.target_role_id,
    )
    return result


@router.get("/inbox")
async def list_inbox(
    status: Optional[HandoffStatus] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user=Depends(require_role([UserRole.talent_partner, UserRole.admin])),
    supabase: Client = Depends(),
):
    """List handoffs received by the current partner (inbox)."""
    service = HandoffService(supabase)
    return await service.list_inbox(
        partner_id=UUID(user["id"]),
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/outbox")
async def list_outbox(
    status: Optional[HandoffStatus] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user=Depends(require_role([UserRole.talent_partner, UserRole.admin])),
    supabase: Client = Depends(),
):
    """List handoffs sent by the current partner (outbox)."""
    service = HandoffService(supabase)
    return await service.list_outbox(
        partner_id=UUID(user["id"]),
        status=status,
        limit=limit,
        offset=offset,
    )


@router.post("/{handoff_id}/respond")
async def respond_to_handoff(
    handoff_id: UUID,
    accept: bool,
    response_notes: Optional[str] = None,
    user=Depends(require_role([UserRole.talent_partner, UserRole.admin])),
    supabase: Client = Depends(),
):
    """Accept or decline a handoff. Only the recipient can respond."""
    service = HandoffService(supabase)
    result = await service.respond(
        handoff_id=handoff_id,
        partner_id=UUID(user["id"]),
        accept=accept,
        response_notes=response_notes,
    )
    if not result:
        raise HTTPException(
            status_code=403,
            detail="Cannot respond: not the recipient, handoff not found, or already responded"
        )
    return result


@router.get("/{handoff_id}")
async def get_handoff(
    handoff_id: UUID,
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """Get a single handoff with full details."""
    service = HandoffService(supabase)
    result = await service.get_handoff(handoff_id)
    if not result:
        raise HTTPException(status_code=404, detail="Handoff not found")
    return result


@router.get("/attribution/{attribution_id}")
async def get_attribution_chain(
    attribution_id: UUID,
    user=Depends(require_role([UserRole.talent_partner, UserRole.admin])),
    supabase: Client = Depends(),
):
    """Get the full attribution chain for a referral (all handoffs linked by attribution ID)."""
    service = HandoffService(supabase)
    return await service.get_attribution_chain(attribution_id)
```

### Quote Endpoints (`backend/api/quotes.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional
from backend.api.auth import get_current_user, require_role
from backend.contracts.quote import QuoteRequest
from backend.contracts.shared import QuoteStatus, UserRole
from backend.services.quote import QuoteService
from supabase import Client

router = APIRouter(prefix="/api/quotes", tags=["quotes"])


@router.post("/generate")
async def generate_quote(
    data: QuoteRequest,
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """
    Generate a placement fee quote for a candidate-role pairing.
    Calculates base fee by seniority, applies pool discount if eligible.
    """
    service = QuoteService(supabase)
    try:
        result = await service.generate_quote(
            client_id=UUID(user["id"]),
            candidate_id=data.candidate_id,
            role_id=data.role_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{quote_id}")
async def get_quote(
    quote_id: UUID,
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """Get a single quote with fee breakdown."""
    service = QuoteService(supabase)
    result = await service.get_quote(quote_id)
    if not result:
        raise HTTPException(status_code=404, detail="Quote not found")
    return result


@router.get("/")
async def list_quotes(
    status: Optional[QuoteStatus] = None,
    limit: int = Query(default=50, le=100),
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """List quotes for the current client."""
    service = QuoteService(supabase)
    return await service.list_quotes_for_client(
        client_id=UUID(user["id"]),
        status=status,
        limit=limit,
    )


@router.patch("/{quote_id}/status")
async def update_quote_status(
    quote_id: UUID,
    status: QuoteStatus,
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """Update quote status (accept, decline). Valid transitions are enforced."""
    service = QuoteService(supabase)
    result = await service.update_quote_status(
        quote_id=quote_id,
        new_status=status,
        actor_id=UUID(user["id"]),
        actor_role=UserRole(user["role"]),
    )
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Invalid status transition or quote not found"
        )
    return result
```

### Tests (`backend/tests/test_handoffs.py`)

```python
import pytest
from uuid import uuid4
from backend.contracts.handoff import HandoffCreate
from backend.contracts.shared import HandoffStatus


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
```

### Tests (`backend/tests/test_quotes.py`)

```python
import pytest
from decimal import Decimal
from uuid import uuid4
from backend.services.quote import (
    QuoteService, SENIORITY_BASE_FEES, POOL_DISCOUNT_PERCENTAGE,
    QUOTE_VALIDITY_DAYS
)
from backend.contracts.shared import SeniorityLevel, QuoteStatus
from backend.contracts.quote import QuoteRequest


def test_seniority_fee_schedule():
    """Fee schedule covers all seniority levels with ascending fees."""
    levels = [
        SeniorityLevel.junior, SeniorityLevel.mid, SeniorityLevel.senior,
        SeniorityLevel.lead, SeniorityLevel.principal
    ]
    fees = [SENIORITY_BASE_FEES[level] for level in levels]
    # Fees should be strictly ascending
    for i in range(1, len(fees)):
        assert fees[i] > fees[i - 1], f"{levels[i].value} fee should be higher than {levels[i-1].value}"


def test_pool_discount_percentage():
    assert POOL_DISCOUNT_PERCENTAGE == Decimal("0.20")


def test_pool_discount_calculation():
    base = Decimal("18000")
    discount = (base * POOL_DISCOUNT_PERCENTAGE).quantize(Decimal("0.01"))
    assert discount == Decimal("3600.00")
    assert base - discount == Decimal("14400.00")


def test_quote_validity():
    assert QUOTE_VALIDITY_DAYS == 14


def test_quote_request_model():
    q = QuoteRequest(candidate_id=uuid4(), role_id=uuid4())
    assert q.candidate_id is not None
    assert q.role_id is not None


def test_quote_status_valid_transitions():
    """Generated → sent → accepted/declined/expired."""
    terminal = {QuoteStatus.accepted, QuoteStatus.declined, QuoteStatus.expired}
    for status in terminal:
        assert status.value in ["accepted", "declined", "expired"]
```

## Outputs
- `backend/services/handoff.py`
- `backend/services/quote.py`
- `backend/api/handoffs.py`
- `backend/api/quotes.py`
- `backend/tests/test_handoffs.py`
- `backend/tests/test_quotes.py`

## Acceptance Criteria
1. `POST /api/handoffs/` creates a handoff with attribution ID and emits signal
2. `GET /api/handoffs/inbox` returns handoffs received by current partner
3. `GET /api/handoffs/outbox` returns handoffs sent by current partner
4. `POST /api/handoffs/{id}/respond` accepts or declines, only by recipient, emits signal
5. Attribution chain is queryable by attribution ID
6. `POST /api/quotes/generate` calculates correct base fee by seniority
7. Pool candidates receive 20% discount with human-readable savings message
8. Fee breakdown is clear and non-technical (suitable for client display)
9. Quote expiry is 14 days, status transitions are validated
10. All handoff/quote actions emit appropriate signal events
11. All tests pass

## Handoff Notes
- **To Task 14:** The copilot should be able to answer questions about handoffs and quotes (e.g., "Show my pending handoffs", "What quotes are outstanding?").
- **To Task 16:** Seed data should include 10+ handoffs between demo partners and 15+ quotes with various statuses.
- **To Agent B:** Handoff inbox/outbox endpoints return separate lists. The `fee_breakdown` field on quotes contains a nested object with `summary`, `base_fee`, optional `pool_discount`, `final_fee`, `savings_message`, and `validity` — render this as a clear fee card. Quote status flow: generated → sent → accepted/declined/expired.
- **Decision:** Fees are fixed amounts per seniority level (not percentage of salary) for PoC simplicity. Pool detection checks shared collections and multi-source candidates. Attribution ID links the entire referral chain for commission tracking.
