import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import CurrentUser, get_current_user, require_role
from api.deps import get_supabase_admin
from contracts.shared import ConfidenceLevel, MatchStatus, UserRole
from matching.engine import MatchingEngine
from matching.explainer import MatchExplainer

logger = logging.getLogger("recruittech.api.matches")
router = APIRouter()


@router.get("/by-role/{role_id}")
async def get_matches_by_role(
    role_id: UUID,
    confidence: Optional[ConfidenceLevel] = None,
    status: Optional[MatchStatus] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(get_current_user),
):
    """Get all matches for a role, ranked by overall score."""
    supabase = get_supabase_admin()
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


@router.get("/by-candidate/{candidate_id}")
async def get_matches_by_candidate(
    candidate_id: UUID,
    confidence: Optional[ConfidenceLevel] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(get_current_user),
):
    """Get all matches for a candidate across all roles."""
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
    """Get a single match with full details."""
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
    return result.data


@router.patch("/{match_id}/status")
async def update_match_status(
    match_id: UUID,
    status: MatchStatus,
    user: CurrentUser = Depends(get_current_user),
):
    """Update match status (shortlist, dismiss, request intro)."""
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

    supabase.table("matches").update({"status": status.value}).eq(
        "id", str(match_id)
    ).execute()

    return {
        "status": "updated",
        "match_id": str(match_id),
        "new_status": status.value,
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
