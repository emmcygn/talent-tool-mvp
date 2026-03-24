from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.auth import CurrentUser, require_role
from api.deps import get_supabase_admin
from contracts.shared import UserRole

router = APIRouter()


# ---- Platform Stats ----

@router.get("/stats")
async def get_platform_stats(
    user: CurrentUser = Depends(require_role(UserRole.admin)),
):
    """
    Platform-wide statistics for the admin dashboard.
    Returns totals and growth metrics.
    """
    supabase = get_supabase_admin()

    # Total counts
    candidates_result = supabase.table("candidates").select("id", count="exact").execute()
    roles_result = supabase.table("roles").select("id", count="exact").execute()
    matches_result = supabase.table("matches").select("id", count="exact").execute()
    handoffs_result = supabase.table("handoffs").select("id", count="exact").execute()
    quotes_result = supabase.table("quotes").select("id", count="exact").execute()
    users_result = supabase.table("users").select("id", count="exact").execute()

    # Active counts
    active_roles = supabase.table("roles").select("id", count="exact") \
        .eq("status", "active").execute()
    pending_handoffs = supabase.table("handoffs").select("id", count="exact") \
        .eq("status", "pending").execute()
    open_quotes = supabase.table("quotes").select("id", count="exact") \
        .in_("status", ["generated", "sent"]).execute()

    # Growth: new records in last 7 days
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    new_candidates = supabase.table("candidates").select("id", count="exact") \
        .gte("created_at", week_ago).execute()
    new_matches = supabase.table("matches").select("id", count="exact") \
        .gte("created_at", week_ago).execute()

    # Placements (from signals)
    placements = supabase.table("signals").select("id", count="exact") \
        .eq("event_type", "placement_made").execute()

    return {
        "totals": {
            "candidates": candidates_result.count or 0,
            "roles": roles_result.count or 0,
            "matches": matches_result.count or 0,
            "handoffs": handoffs_result.count or 0,
            "quotes": quotes_result.count or 0,
            "users": users_result.count or 0,
            "placements": placements.count or 0,
        },
        "active": {
            "active_roles": active_roles.count or 0,
            "pending_handoffs": pending_handoffs.count or 0,
            "open_quotes": open_quotes.count or 0,
        },
        "growth_7d": {
            "new_candidates": new_candidates.count or 0,
            "new_matches": new_matches.count or 0,
        },
    }


# ---- Adapter Health ----

# In-memory adapter health registry (populated by adapters on sync)
_adapter_health: dict[str, dict] = {}


def update_adapter_health(adapter_name: str, status: dict):
    """Called by adapters after sync to report health. See adapters/base.py."""
    _adapter_health[adapter_name] = {
        **status,
        "reported_at": datetime.utcnow().isoformat(),
    }


@router.get("/adapters/health")
async def get_adapter_health(
    user: CurrentUser = Depends(require_role(UserRole.admin)),
):
    """
    Get health status for all registered adapters.
    Each adapter reports: last sync time, records processed, error count, status.
    """
    # Return known adapters with defaults if not yet reported
    default_adapters = ["bullhorn", "hubspot", "linkedin"]
    result = []

    for name in default_adapters:
        if name in _adapter_health:
            result.append({"adapter_name": name, **_adapter_health[name]})
        else:
            result.append({
                "adapter_name": name,
                "status": "unknown",
                "last_sync": None,
                "records_processed": 0,
                "error_count": 0,
                "errors": [],
                "reported_at": None,
            })

    return result


@router.post("/adapters/{adapter_name}/sync")
async def trigger_adapter_sync(
    adapter_name: str,
    user: CurrentUser = Depends(require_role(UserRole.admin)),
):
    """Trigger a re-sync for a specific adapter."""
    from adapters.registry import adapter_registry

    try:
        adapter = adapter_registry.get(adapter_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Adapter '{adapter_name}' not found")

    try:
        result = await adapter.sync()
        update_adapter_health(adapter_name, {
            "status": "healthy",
            "last_sync": datetime.utcnow().isoformat(),
            "records_processed": result.get("records", 0),
            "error_count": 0,
            "errors": [],
        })
        return {"adapter": adapter_name, "status": "synced", **result}
    except Exception as e:
        update_adapter_health(adapter_name, {
            "status": "error",
            "last_sync": datetime.utcnow().isoformat(),
            "records_processed": 0,
            "error_count": 1,
            "errors": [str(e)],
        })
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ---- AI Pipeline Monitoring ----

@router.get("/pipeline/status")
async def get_pipeline_status(
    user: CurrentUser = Depends(require_role(UserRole.admin)),
):
    """
    AI pipeline monitoring: extraction queue, processing stats, confidence distribution.
    """
    supabase = get_supabase_admin()

    # Candidates pending extraction (no skills extracted yet)
    pending = supabase.table("candidates").select("id", count="exact") \
        .is_("extraction_confidence", "null").execute()

    # Candidates with low confidence (need review)
    low_confidence = (
        supabase.table("candidates")
        .select("id", count="exact")
        .lt("extraction_confidence", 0.7)
        .not_.is_("extraction_confidence", "null")
        .execute()
    )

    # Candidates fully processed
    processed = supabase.table("candidates").select("id", count="exact") \
        .gte("extraction_confidence", 0.7).execute()

    # Confidence distribution
    all_candidates = (
        supabase.table("candidates")
        .select("extraction_confidence")
        .not_.is_("extraction_confidence", "null")
        .execute()
    )

    confidence_buckets = {"high": 0, "medium": 0, "low": 0}
    for c in (all_candidates.data or []):
        conf = c.get("extraction_confidence", 0)
        if conf >= 0.8:
            confidence_buckets["high"] += 1
        elif conf >= 0.6:
            confidence_buckets["medium"] += 1
        else:
            confidence_buckets["low"] += 1

    # Embedding coverage
    with_embedding = (
        supabase.table("candidates")
        .select("id", count="exact")
        .not_.is_("embedding", "null")
        .execute()
    )
    total_candidates = supabase.table("candidates").select("id", count="exact").execute()

    return {
        "extraction_queue": {
            "pending": pending.count or 0,
            "low_confidence_review": low_confidence.count or 0,
            "processed": processed.count or 0,
        },
        "confidence_distribution": confidence_buckets,
        "embedding_coverage": {
            "with_embedding": with_embedding.count or 0,
            "total": total_candidates.count or 0,
            "percentage": round(
                ((with_embedding.count or 0) / max(total_candidates.count or 1, 1)) * 100, 1
            ),
        },
    }


# ---- Dedup Review Queue ----

@router.get("/dedup/queue")
async def get_dedup_queue(
    status: str = Query(default="pending", pattern="^(pending|approved|rejected)$"),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_role(UserRole.admin)),
):
    """
    Get the deduplication review queue.
    Returns candidate pairs flagged as potential duplicates.
    """
    supabase = get_supabase_admin()
    query = (
        supabase.table("dedup_queue")
        .select("*")
        .eq("status", status)
        .order("confidence", desc=True)
        .range(offset, offset + limit - 1)
    )

    result = query.execute()

    # Enrich with candidate summaries
    enriched = []
    for item in (result.data or []):
        candidate_a = (
            supabase.table("candidates")
            .select("id, first_name, last_name, email, location, skills")
            .eq("id", item["candidate_a_id"])
            .single()
            .execute()
        )
        candidate_b = (
            supabase.table("candidates")
            .select("id, first_name, last_name, email, location, skills")
            .eq("id", item["candidate_b_id"])
            .single()
            .execute()
        )

        enriched.append({
            **item,
            "candidate_a": candidate_a.data,
            "candidate_b": candidate_b.data,
        })

    return enriched


class DedupDecision(BaseModel):
    action: str  # "merge" | "keep_separate"
    primary_id: UUID | None = None  # which record to keep as primary (for merge)
    notes: str | None = None


@router.post("/dedup/{queue_item_id}/resolve")
async def resolve_dedup(
    queue_item_id: UUID,
    decision: DedupDecision,
    user: CurrentUser = Depends(require_role(UserRole.admin)),
):
    """
    Resolve a dedup queue item: merge the candidates or keep them separate.
    """
    supabase = get_supabase_admin()

    # Load queue item
    item = (
        supabase.table("dedup_queue")
        .select("*")
        .eq("id", str(queue_item_id))
        .single()
        .execute()
    )
    if not item.data:
        raise HTTPException(status_code=404, detail="Queue item not found")

    if decision.action == "merge":
        # Perform merge: keep primary, merge secondary's unique data
        primary_id = (
            str(decision.primary_id)
            if decision.primary_id
            else item.data["candidate_a_id"]
        )
        secondary_id = (
            item.data["candidate_b_id"]
            if primary_id == item.data["candidate_a_id"]
            else item.data["candidate_a_id"]
        )

        # Load both candidates
        primary = (
            supabase.table("candidates").select("*").eq("id", primary_id).single().execute()
        )
        secondary = (
            supabase.table("candidates").select("*").eq("id", secondary_id).single().execute()
        )

        if primary.data and secondary.data:
            # Merge: combine skills, sources, experience; keep most recent data
            merged_skills = _merge_skills(
                primary.data.get("skills", []),
                secondary.data.get("skills", []),
            )
            merged_sources = (primary.data.get("sources") or []) + (
                secondary.data.get("sources") or []
            )
            merged_experience = _merge_experience(
                primary.data.get("experience", []),
                secondary.data.get("experience", []),
            )

            # Update primary with merged data
            supabase.table("candidates").update({
                "skills": merged_skills,
                "sources": merged_sources,
                "experience": merged_experience,
                "dedup_group": primary_id,
                "dedup_confidence": item.data.get("confidence", 0.9),
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", primary_id).execute()

            # Mark secondary as merged (soft delete via dedup_group)
            supabase.table("candidates").update({
                "dedup_group": primary_id,
            }).eq("id", secondary_id).execute()

        new_status = "approved"
    else:
        new_status = "rejected"

    # Update queue item
    supabase.table("dedup_queue").update({
        "status": new_status,
        "resolved_by": str(user.id),
        "resolved_at": datetime.utcnow().isoformat(),
        "resolution_notes": decision.notes,
    }).eq("id", str(queue_item_id)).execute()

    return {"status": new_status, "queue_item_id": str(queue_item_id)}


# ---- User Management ----

class UserCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    role: UserRole
    organisation_id: UUID | None = None


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


@router.get("/users")
async def list_users(
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(default=50, le=100),
    user: CurrentUser = Depends(require_role(UserRole.admin)),
):
    """List all users with optional role and status filters."""
    supabase = get_supabase_admin()
    query = (
        supabase.table("users")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
    )

    if role:
        query = query.eq("role", role.value)
    if is_active is not None:
        query = query.eq("is_active", is_active)

    result = query.execute()
    return result.data or []


@router.get("/users/{user_id}")
async def get_user(
    user_id: UUID,
    user: CurrentUser = Depends(require_role(UserRole.admin)),
):
    """Get a single user with activity summary."""
    supabase = get_supabase_admin()
    result = (
        supabase.table("users").select("*").eq("id", str(user_id)).single().execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    # Get activity summary from signals
    signals = (
        supabase.table("signals")
        .select("event_type", count="exact")
        .eq("actor_id", str(user_id))
        .execute()
    )

    user_data = dict(result.data)
    user_data["total_actions"] = signals.count or 0

    return user_data


@router.post("/users")
async def create_user(
    data: UserCreate,
    user: CurrentUser = Depends(require_role(UserRole.admin)),
):
    """Create a new user account."""
    supabase = get_supabase_admin()
    user_id = uuid4()
    now = datetime.utcnow().isoformat()

    record = {
        "id": str(user_id),
        "email": data.email,
        "first_name": data.first_name,
        "last_name": data.last_name,
        "role": data.role.value,
        "organisation_id": str(data.organisation_id) if data.organisation_id else None,
        "is_active": True,
        "created_at": now,
    }

    result = supabase.table("users").insert(record).execute()
    return result.data[0] if result.data else record


@router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    user: CurrentUser = Depends(require_role(UserRole.admin)),
):
    """Update user details (name, role, active status)."""
    supabase = get_supabase_admin()
    update = {}
    if data.first_name is not None:
        update["first_name"] = data.first_name
    if data.last_name is not None:
        update["last_name"] = data.last_name
    if data.role is not None:
        update["role"] = data.role.value
    if data.is_active is not None:
        update["is_active"] = data.is_active

    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = (
        supabase.table("users").update(update).eq("id", str(user_id)).execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    return result.data[0]


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: UUID,
    user: CurrentUser = Depends(require_role(UserRole.admin)),
):
    """Deactivate a user (soft delete — sets is_active to false)."""
    supabase = get_supabase_admin()
    result = (
        supabase.table("users").update({"is_active": False}).eq("id", str(user_id)).execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "deactivated", "user_id": str(user_id)}


# ---- Helper Functions ----

def _merge_skills(skills_a: list, skills_b: list) -> list:
    """Merge two skill lists, deduplicating by name, keeping higher years."""
    skill_map: dict = {}
    for s in skills_a:
        if isinstance(s, dict):
            skill_map[s.get("name", "").lower()] = s
    for s in skills_b:
        if isinstance(s, dict):
            name = s.get("name", "").lower()
            if name in skill_map:
                # Keep the one with more years
                existing_years = skill_map[name].get("years") or 0
                new_years = s.get("years") or 0
                if new_years > existing_years:
                    skill_map[name] = s
            else:
                skill_map[name] = s
    return list(skill_map.values())


def _merge_experience(exp_a: list, exp_b: list) -> list:
    """Merge experience lists, deduplicating by company+title."""
    seen: set = set()
    merged = []
    for e in exp_a + exp_b:
        if isinstance(e, dict):
            key = (e.get("company", "").lower(), e.get("title", "").lower())
            if key not in seen:
                seen.add(key)
                merged.append(e)
    return merged
