from datetime import datetime
from uuid import UUID, uuid4

from contracts.shared import SignalType, UserRole


class SignalTracker:
    """Emits and queries signal events for activity tracking."""

    def __init__(self, supabase):
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
        if isinstance(event_type, SignalType):
            event_type = event_type.value
        if isinstance(actor_role, UserRole):
            actor_role = actor_role.value

        record = {
            "id": str(uuid4()),
            "event_type": event_type,
            "actor_id": str(actor_id),
            "actor_role": actor_role,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "metadata": metadata or {},
        }
        result = self.supabase.table("signals").insert(record).execute()
        return result.data[0] if result.data else record

    async def emit_batch(self, signals: list[dict]) -> int:
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
        query = (
            self.supabase.table("signals")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
        )
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
        self, entity_type: str, entity_id: UUID, limit: int = 100
    ) -> list[dict]:
        result = (
            self.supabase.table("signals")
            .select("*")
            .eq("entity_type", entity_type)
            .eq("entity_id", str(entity_id))
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
