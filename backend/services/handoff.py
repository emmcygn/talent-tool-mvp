from datetime import datetime
from uuid import UUID, uuid4

from contracts.shared import HandoffStatus, SignalType, UserRole
from signals.tracker import SignalTracker
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
        query = (
            self.supabase.table("handoffs")
            .select("*")
            .eq("to_partner_id", str(partner_id))
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )

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
        query = (
            self.supabase.table("handoffs")
            .select("*")
            .eq("from_partner_id", str(partner_id))
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )

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
        existing = (
            self.supabase.table("handoffs")
            .select("*")
            .eq("id", str(handoff_id))
            .single()
            .execute()
        )

        if not existing.data:
            return None
        if existing.data["to_partner_id"] != str(partner_id):
            return None
        if existing.data["status"] != HandoffStatus.pending.value:
            return None  # Already responded

        new_status = HandoffStatus.accepted if accept else HandoffStatus.declined
        now = datetime.utcnow().isoformat()

        result = (
            self.supabase.table("handoffs")
            .update({
                "status": new_status.value,
                "response_notes": response_notes,
                "responded_at": now,
            })
            .eq("id", str(handoff_id))
            .execute()
        )

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
        result = (
            self.supabase.table("handoffs")
            .select("*")
            .eq("id", str(handoff_id))
            .single()
            .execute()
        )
        return result.data

    async def get_attribution_chain(self, attribution_id: UUID) -> list[dict]:
        """
        Get all handoffs in an attribution chain.
        Tracks the referral path from original ingestion to placement.
        """
        result = (
            self.supabase.table("handoffs")
            .select("*")
            .eq("attribution_id", str(attribution_id))
            .order("created_at", desc=False)
            .execute()
        )
        return result.data or []

    def _compute_response_time(self, created_at: str, responded_at: str) -> int:
        """Compute response time in seconds."""
        try:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            responded = datetime.fromisoformat(responded_at.replace("Z", "+00:00"))
            return int((responded - created).total_seconds())
        except Exception:
            return 0
