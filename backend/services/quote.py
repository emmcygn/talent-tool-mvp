from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from contracts.shared import QuoteStatus, SeniorityLevel, SignalType, UserRole
from signals.tracker import SignalTracker
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
        role_result = (
            self.supabase.table("roles")
            .select("seniority, title, salary_band")
            .eq("id", str(role_id))
            .single()
            .execute()
        )
        role = role_result.data
        if not role:
            raise ValueError(f"Role {role_id} not found")

        # Load candidate to check pool status
        candidate_result = (
            self.supabase.table("candidates")
            .select("id, first_name, last_name, sources")
            .eq("id", str(candidate_id))
            .single()
            .execute()
        )
        candidate = candidate_result.data
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        # Determine seniority
        seniority = (
            SeniorityLevel(role["seniority"])
            if role.get("seniority")
            else SeniorityLevel.mid
        )
        base_fee = SENIORITY_BASE_FEES.get(seniority, SENIORITY_BASE_FEES[SeniorityLevel.mid])

        # Check if candidate is in shared pool
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
        result = (
            self.supabase.table("quotes")
            .select("*")
            .eq("id", str(quote_id))
            .single()
            .execute()
        )
        return result.data

    async def list_quotes_for_client(
        self,
        client_id: UUID,
        status: QuoteStatus | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """List all quotes for a client."""
        query = (
            self.supabase.table("quotes")
            .select("*")
            .eq("client_id", str(client_id))
            .order("created_at", desc=True)
            .limit(limit)
        )

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
        Returns None if quote not found or transition is invalid.
        """
        existing = (
            self.supabase.table("quotes")
            .select("*")
            .eq("id", str(quote_id))
            .single()
            .execute()
        )
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

        result = (
            self.supabase.table("quotes")
            .update({"status": new_status.value})
            .eq("id", str(quote_id))
            .execute()
        )

        return result.data[0] if result.data else None

    async def check_and_expire_quotes(self) -> int:
        """
        Expire quotes past their expiry date.
        Should be called periodically (e.g., via a scheduled task or on access).
        """
        now = datetime.utcnow().isoformat()

        # Find non-terminal quotes past expiry
        result = (
            self.supabase.table("quotes")
            .select("id")
            .in_("status", [QuoteStatus.generated.value, QuoteStatus.sent.value])
            .lt("expires_at", now)
            .execute()
        )

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
        collection_result = (
            self.supabase.table("collection_candidates")
            .select("collection_id")
            .eq("candidate_id", str(candidate_id))
            .execute()
        )

        if collection_result.data:
            collection_ids = [c["collection_id"] for c in collection_result.data]
            shared_result = (
                self.supabase.table("collections")
                .select("id")
                .in_("id", collection_ids)
                .in_("visibility", ["shared_all", "shared_specific"])
                .execute()
            )
            if shared_result.data:
                return True

        # Check if candidate has multiple sources
        candidate = (
            self.supabase.table("candidates")
            .select("sources")
            .eq("id", str(candidate_id))
            .single()
            .execute()
        )
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
        breakdown: dict = {
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
            breakdown["savings_message"] = (
                f"You save £{pool_discount:,.2f} because this candidate is already in our talent network"
            )

        breakdown["final_fee"] = {
            "amount": str(final_fee),
            "currency": "GBP",
            "description": (
                "Total placement fee"
                if not is_pool
                else "Total placement fee (after network discount)"
            ),
        }

        breakdown["validity"] = f"This quote is valid for {QUOTE_VALIDITY_DAYS} days"

        return breakdown
