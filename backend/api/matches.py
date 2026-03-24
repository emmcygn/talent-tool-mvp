import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.auth import CurrentUser, get_current_user, require_role
from api.deps import get_supabase_admin
from contracts.shared import ConfidenceLevel, MatchStatus, UserRole
from matching.engine import MatchingEngine
from matching.explainer import MatchExplainer

logger = logging.getLogger("recruittech.api.matches")
router = APIRouter()


class MatchStatusUpdate(BaseModel):
    """Request body for updating match status."""

    status: MatchStatus
    reason: str | None = None


@router.get("/role/{role_id}")
async def get_matches_by_role(
    role_id: UUID,
    confidence: Optional[ConfidenceLevel] = None,
    status: Optional[MatchStatus] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(get_current_user),
):
    """Get all matches for a role, ranked by overall score.

    Clients can only see matches for their own roles.
    Talent partners and admins can see all.
    """
    supabase = get_supabase_admin()

    # Clients: verify they own the role
    if user.role == UserRole.client:
        role_check = (
            supabase.table("roles")
            .select("id, created_by")
            .eq("id", str(role_id))
            .single()
            .execute()
        )
        if not role_check.data or role_check.data["created_by"] != str(user.id):
            raise HTTPException(status_code=403, detail="Access denied")

    query = (
        supabase.table("matches")
        .select("*")
        .eq("role_id", str(role_id))
        .order("overall_score", desc=True)
        .range(offset, offset + limit - 1)
    )
    if confidence:
        query = query.eq("confidence", confidence.value)
    if status:
        query = query.eq("status", status.value)

    result = query.execute()
    return result.data or []


@router.get("/role/{role_id}/anonymized")
async def get_matches_by_role_anonymized(
    role_id: UUID,
    confidence: Optional[ConfidenceLevel] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(get_current_user),
):
    """Get matches for a role with anonymized candidate data (for clients)."""
    supabase = get_supabase_admin()

    # Clients: verify they own the role
    if user.role == UserRole.client:
        role_check = (
            supabase.table("roles")
            .select("id, created_by")
            .eq("id", str(role_id))
            .single()
            .execute()
        )
        if not role_check.data or role_check.data["created_by"] != str(user.id):
            raise HTTPException(status_code=403, detail="Access denied")

    query = (
        supabase.table("matches")
        .select("*")
        .eq("role_id", str(role_id))
        .order("overall_score", desc=True)
        .range(offset, offset + limit - 1)
    )
    if confidence:
        query = query.eq("confidence", confidence.value)

    matches_result = query.execute()
    matches = matches_result.data or []

    # Load candidates and anonymize
    candidate_ids = list({m["candidate_id"] for m in matches})
    if not candidate_ids:
        return []

    candidates_result = (
        supabase.table("candidates")
        .select("id, first_name, last_name, location, skills, seniority, availability, industries, experience, sources")
        .in_("id", candidate_ids)
        .execute()
    )
    candidates_map = {c["id"]: c for c in (candidates_result.data or [])}

    results = []
    for match in matches:
        candidate = candidates_map.get(match["candidate_id"])
        if not candidate:
            continue

        experience = candidate.get("experience") or []
        total_months = sum(
            (e.get("duration_months", 0) or 0)
            for e in experience
            if isinstance(e, dict)
        )

        anon_candidate = {
            "id": candidate["id"],
            "first_name": candidate.get("first_name", ""),
            "last_initial": candidate.get("last_name", "?")[0],
            "location": candidate.get("location"),
            "skills": candidate.get("skills", []),
            "seniority": candidate.get("seniority"),
            "availability": candidate.get("availability"),
            "industries": candidate.get("industries", []),
            "experience_years": total_months // 12 if total_months else None,
            "is_pool_candidate": len(candidate.get("sources", [])) > 1,
        }
        results.append({"match": match, "candidate": anon_candidate})

    return results


@router.get("/candidate/{candidate_id}")
async def get_matches_by_candidate(
    candidate_id: UUID,
    confidence: Optional[ConfidenceLevel] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(
        require_role(UserRole.talent_partner, UserRole.admin)
    ),
):
    """Get all matches for a candidate. Talent partners and admins only."""
    supabase = get_supabase_admin()
    query = (
        supabase.table("matches")
        .select("*")
        .eq("candidate_id", str(candidate_id))
        .order("overall_score", desc=True)
        .range(offset, offset + limit - 1)
    )
    if confidence:
        query = query.eq("confidence", confidence.value)

    result = query.execute()
    return result.data or []


@router.get("/{match_id}")
async def get_match(
    match_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    """Get a single match with full details.

    Clients can only access matches for their own roles.
    """
    supabase = get_supabase_admin()
    result = (
        supabase.table("matches")
        .select("*")
        .eq("id", str(match_id))
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Match not found")

    # Clients: verify they own the associated role
    if user.role == UserRole.client:
        role_check = (
            supabase.table("roles")
            .select("id, created_by")
            .eq("id", result.data["role_id"])
            .single()
            .execute()
        )
        if not role_check.data or role_check.data["created_by"] != str(user.id):
            raise HTTPException(status_code=403, detail="Access denied")

    return result.data


@router.patch("/{match_id}/status")
async def update_match_status(
    match_id: UUID,
    body: MatchStatusUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    """Update match status (shortlist, dismiss, request intro).

    Accepts { status, reason } JSON body.
    """
    supabase = get_supabase_admin()

    match_result = (
        supabase.table("matches")
        .select("*")
        .eq("id", str(match_id))
        .single()
        .execute()
    )
    if not match_result.data:
        raise HTTPException(status_code=404, detail="Match not found")

    # Clients: verify they own the associated role
    if user.role == UserRole.client:
        role_check = (
            supabase.table("roles")
            .select("id, created_by")
            .eq("id", match_result.data["role_id"])
            .single()
            .execute()
        )
        if not role_check.data or role_check.data["created_by"] != str(user.id):
            raise HTTPException(status_code=403, detail="Access denied")

    # Persist status and reason in scoring_breakdown metadata
    existing_breakdown = match_result.data.get("scoring_breakdown") or {}
    if body.reason:
        existing_breakdown["status_reason"] = body.reason

    update_data = {
        "status": body.status.value,
        "scoring_breakdown": existing_breakdown,
    }
    supabase.table("matches").update(update_data).eq(
        "id", str(match_id)
    ).execute()

    # Emit signal for analytics tracking
    from signals.tracker import SignalTracker

    signal_type_map = {
        MatchStatus.shortlisted: "candidate_shortlisted",
        MatchStatus.dismissed: "candidate_dismissed",
        MatchStatus.intro_requested: "intro_requested",
    }
    if body.status in signal_type_map:
        tracker = SignalTracker(supabase)
        await tracker.emit(
            event_type=signal_type_map[body.status],
            actor_id=user.id,
            actor_role=user.role,
            entity_type="match",
            entity_id=match_id,
            metadata={
                "role_id": match_result.data["role_id"],
                "candidate_id": match_result.data["candidate_id"],
                "reason": body.reason,
            },
        )

    return {
        "status": "updated",
        "match_id": str(match_id),
        "new_status": body.status.value,
    }


@router.post("/generate/{role_id}")
async def trigger_matching(
    role_id: UUID,
    user: CurrentUser = Depends(
        require_role(UserRole.talent_partner, UserRole.admin)
    ),
):
    """Trigger matching pipeline for a role."""
    supabase = get_supabase_admin()
    engine = MatchingEngine(supabase)
    matches = await engine.run_matching(role_id)

    explainer = MatchExplainer(supabase)
    explanation_count = await explainer.generate_explanations(
        role_id=role_id, min_confidence=ConfidenceLevel.good
    )

    return {
        "role_id": str(role_id),
        "matches_generated": len(matches),
        "explanations_generated": explanation_count,
        "breakdown": {
            "strong": sum(
                1
                for m in matches
                if m.confidence == ConfidenceLevel.strong
            ),
            "good": sum(
                1
                for m in matches
                if m.confidence == ConfidenceLevel.good
            ),
            "possible": sum(
                1
                for m in matches
                if m.confidence == ConfidenceLevel.possible
            ),
        },
    }


@router.post("/{match_id}/regenerate-explanation")
async def regenerate_explanation(
    match_id: UUID,
    user: CurrentUser = Depends(
        require_role(UserRole.talent_partner, UserRole.admin)
    ),
):
    """Re-generate explanation for a single match."""
    supabase = get_supabase_admin()
    explainer = MatchExplainer(supabase)
    result = await explainer.generate_single_explanation(match_id)
    if not result:
        raise HTTPException(status_code=404, detail="Match not found")
    return {"match_id": str(match_id), "explanation": result}
