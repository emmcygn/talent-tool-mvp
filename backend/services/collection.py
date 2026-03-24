from datetime import datetime
from uuid import UUID, uuid4

from contracts.collection import CollectionCreate
from contracts.shared import AvailabilityStatus, Visibility


class CollectionService:
    """Business logic for collection management."""

    def __init__(self, supabase):
        self.supabase = supabase

    async def create_collection(
        self, data: CollectionCreate, owner_id: UUID
    ) -> dict | None:
        now = datetime.utcnow().isoformat()
        record = {
            "id": str(uuid4()),
            "name": data.name,
            "description": data.description,
            "owner_id": str(owner_id),
            "visibility": data.visibility.value,
            "shared_with": (
                [str(uid) for uid in data.shared_with]
                if data.shared_with
                else None
            ),
            "tags": data.tags,
        }
        result = self.supabase.table("collections").insert(record).execute()
        return result.data[0] if result.data else None

    async def list_collections(
        self, user_id: UUID, user_role: str, include_shared: bool = True
    ) -> list[dict]:
        if user_role == "admin":
            result = (
                self.supabase.table("collections")
                .select("*")
                .order("updated_at", desc=True)
                .execute()
            )
            return result.data or []

        own_result = (
            self.supabase.table("collections")
            .select("*")
            .eq("owner_id", str(user_id))
            .order("updated_at", desc=True)
            .execute()
        )
        collections = own_result.data or []

        if include_shared:
            shared_all = (
                self.supabase.table("collections")
                .select("*")
                .eq("visibility", Visibility.shared_all.value)
                .neq("owner_id", str(user_id))
                .execute()
            )
            collections.extend(shared_all.data or [])

            shared_specific = (
                self.supabase.table("collections")
                .select("*")
                .eq("visibility", Visibility.shared_specific.value)
                .neq("owner_id", str(user_id))
                .execute()
            )
            for c in shared_specific.data or []:
                shared_list = c.get("shared_with") or []
                if str(user_id) in shared_list:
                    collections.append(c)

        seen = set()
        unique = []
        for c in collections:
            if c["id"] not in seen:
                seen.add(c["id"])
                unique.append(c)
        return unique

    async def get_collection(self, collection_id: UUID) -> dict | None:
        result = (
            self.supabase.table("collections")
            .select("*")
            .eq("id", str(collection_id))
            .single()
            .execute()
        )
        if not result.data:
            return None

        candidates = (
            self.supabase.table("collection_candidates")
            .select("candidate_id")
            .eq("collection_id", str(collection_id))
            .execute()
        )
        result.data["candidate_ids"] = [
            c["candidate_id"] for c in (candidates.data or [])
        ]
        return result.data

    async def add_candidates(
        self, collection_id: UUID, candidate_ids: list[UUID]
    ) -> dict:
        added = 0
        for cid in candidate_ids:
            try:
                self.supabase.table("collection_candidates").insert(
                    {
                        "collection_id": str(collection_id),
                        "candidate_id": str(cid),
                    }
                ).execute()
                added += 1
            except Exception:
                pass
        await self.recompute_stats(collection_id)
        return {"collection_id": str(collection_id), "added": added}

    async def remove_candidates(
        self, collection_id: UUID, candidate_ids: list[UUID]
    ) -> dict:
        for cid in candidate_ids:
            (
                self.supabase.table("collection_candidates")
                .delete()
                .eq("collection_id", str(collection_id))
                .eq("candidate_id", str(cid))
                .execute()
            )
        await self.recompute_stats(collection_id)
        return {"collection_id": str(collection_id), "removed": len(candidate_ids)}

    async def recompute_stats(self, collection_id: UUID) -> dict:
        candidates_result = (
            self.supabase.table("collection_candidates")
            .select("candidate_id")
            .eq("collection_id", str(collection_id))
            .execute()
        )
        candidate_ids = [
            c["candidate_id"] for c in (candidates_result.data or [])
        ]
        candidate_count = len(candidate_ids)

        avg_match_score = None
        available_now_count = 0

        if candidate_ids:
            matches_result = (
                self.supabase.table("matches")
                .select("overall_score")
                .in_("candidate_id", candidate_ids)
                .execute()
            )
            scores = [
                m["overall_score"]
                for m in (matches_result.data or [])
                if m.get("overall_score")
            ]
            if scores:
                avg_match_score = round(sum(scores) / len(scores), 4)

            available_result = (
                self.supabase.table("candidates")
                .select("id, availability")
                .in_("id", candidate_ids)
                .in_(
                    "availability",
                    [
                        AvailabilityStatus.immediate.value,
                        AvailabilityStatus.one_month.value,
                    ],
                )
                .execute()
            )
            available_now_count = len(available_result.data or [])

        self.supabase.table("collections").update(
            {
                "candidate_count": candidate_count,
                "avg_match_score": avg_match_score,
                "available_now_count": available_now_count,
            }
        ).eq("id", str(collection_id)).execute()

        return {
            "candidate_count": candidate_count,
            "avg_match_score": avg_match_score,
            "available_now_count": available_now_count,
        }
