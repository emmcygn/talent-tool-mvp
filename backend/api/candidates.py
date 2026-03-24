import logging
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from api.auth import CurrentUser, get_current_user, require_role
from api.deps import PaginatedResponse, get_supabase_admin
from contracts.candidate import CandidateAnonymized, CandidateCreate
from contracts.shared import AvailabilityStatus, SeniorityLevel, UserRole
from pipelines.deduplicate import DeduplicationPipeline
from pipelines.enrich import ExtractionPipeline

logger = logging.getLogger("recruittech.api.candidates")
router = APIRouter()

extraction_pipeline = ExtractionPipeline()
dedup_pipeline = DeduplicationPipeline()


@router.get("", response_model=PaginatedResponse)
async def list_candidates(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    seniority: Optional[SeniorityLevel] = None,
    availability: Optional[AvailabilityStatus] = None,
    location: Optional[str] = None,
    skill: Optional[str] = None,
    user: CurrentUser = Depends(
        require_role(UserRole.talent_partner, UserRole.admin)
    ),
):
    """List candidates with optional filters."""
    supabase = get_supabase_admin()
    offset = (page - 1) * page_size

    query = supabase.table("candidates").select("*", count="exact")

    if seniority:
        query = query.eq("seniority", seniority.value)
    if availability:
        query = query.eq("availability", availability.value)
    if location:
        query = query.ilike("location", f"%{location}%")
    if skill:
        query = query.contains("skills", [{"name": skill}])

    # Exclude non-primary dedup records
    query = query.or_("dedup_confidence.gt.0,dedup_confidence.is.null")

    query = query.order("created_at", desc=True).range(
        offset, offset + page_size - 1
    )

    result = query.execute()
    total = result.count or 0

    return PaginatedResponse(
        data=result.data or [],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/search", response_model=PaginatedResponse)
async def search_candidates(
    q: Optional[str] = Query(
        default=None, description="Free text search query"
    ),
    skills: Optional[str] = Query(
        default=None, description="Comma-separated skill names"
    ),
    seniority: Optional[SeniorityLevel] = None,
    availability: Optional[AvailabilityStatus] = None,
    location: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: CurrentUser = Depends(
        require_role(UserRole.talent_partner, UserRole.admin)
    ),
):
    """Search candidates with text query and structured filters."""
    supabase = get_supabase_admin()
    offset = (page - 1) * page_size

    query = supabase.table("candidates").select("*", count="exact")
    query = query.or_("dedup_confidence.gt.0,dedup_confidence.is.null")

    if q:
        search_term = f"%{q}%"
        query = query.or_(
            f"first_name.ilike.{search_term},"
            f"last_name.ilike.{search_term},"
            f"cv_text.ilike.{search_term},"
            f"profile_text.ilike.{search_term}"
        )

    if skills:
        skill_list = [s.strip() for s in skills.split(",")]
        for skill_name in skill_list:
            query = query.contains("skills", [{"name": skill_name}])

    if seniority:
        query = query.eq("seniority", seniority.value)
    if availability:
        query = query.eq("availability", availability.value)
    if location:
        query = query.ilike("location", f"%{location}%")

    query = query.order("created_at", desc=True).range(
        offset, offset + page_size - 1
    )

    result = query.execute()
    total = result.count or 0

    return PaginatedResponse(
        data=result.data or [],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    """Get a single candidate by ID.

    Talent partners/admins see full data.
    Clients see anonymized view (only if candidate is matched to their role).
    """
    supabase = get_supabase_admin()

    result = (
        supabase.table("candidates")
        .select("*")
        .eq("id", str(candidate_id))
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate = result.data

    # Client gets anonymized view
    if user.role == UserRole.client:
        match_check = (
            supabase.table("matches")
            .select("id")
            .eq("candidate_id", str(candidate_id))
            .execute()
        )
        role_check = (
            supabase.table("roles")
            .select("id")
            .eq("created_by", str(user.id))
            .execute()
        )
        client_role_ids = {r["id"] for r in (role_check.data or [])}
        has_access = any(
            m.get("role_id") in client_role_ids
            for m in (match_check.data or [])
        )

        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")

        experience = candidate.get("experience", [])
        total_months = sum(
            e.get("duration_months", 0) or 0 for e in experience
        )
        total_years = total_months // 12 if total_months else None

        return CandidateAnonymized(
            id=candidate["id"],
            first_name=candidate.get("first_name", ""),
            last_initial=candidate.get("last_name", "?")[0],
            location=candidate.get("location"),
            skills=candidate.get("skills", []),
            seniority=candidate.get("seniority"),
            availability=candidate.get("availability"),
            industries=candidate.get("industries", []),
            experience_years=total_years,
            is_pool_candidate=len(candidate.get("sources", [])) > 1,
        )

    return candidate


@router.post("", status_code=201)
async def create_candidate(
    body: CandidateCreate,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(
        require_role(UserRole.talent_partner, UserRole.admin)
    ),
):
    """Create a new candidate. Triggers extraction + dedup in background."""
    supabase = get_supabase_admin()

    candidate_id = uuid4()
    record = {
        "id": str(candidate_id),
        "first_name": body.first_name,
        "last_name": body.last_name,
        "email": body.email,
        "phone": body.phone,
        "location": body.location,
        "linkedin_url": body.linkedin_url,
        "cv_text": body.cv_text,
        "profile_text": body.profile_text,
        "skills": [],
        "experience": [],
        "industries": [],
        "sources": [],
        "extraction_flags": [],
        "created_by": str(user.id),
    }

    result = supabase.table("candidates").insert(record).execute()

    if not result.data:
        raise HTTPException(
            status_code=500, detail="Failed to create candidate"
        )

    created = result.data[0]

    background_tasks.add_task(
        _run_post_create_pipeline, candidate_id, user.id
    )

    return created


async def _run_post_create_pipeline(candidate_id: UUID, user_id: UUID):
    """Background task: run extraction then dedup after candidate creation."""
    try:
        logger.info(f"Running extraction for candidate {candidate_id}")
        await extraction_pipeline.extract_candidate(candidate_id)

        logger.info(f"Running dedup for candidate {candidate_id}")
        await dedup_pipeline.run(candidate_ids=[candidate_id])
    except Exception as e:
        logger.error(
            f"Post-create pipeline failed for {candidate_id}: {e}"
        )


@router.patch("/{candidate_id}")
async def update_candidate(
    candidate_id: UUID,
    body: dict,
    user: CurrentUser = Depends(
        require_role(UserRole.talent_partner, UserRole.admin)
    ),
):
    """Update a candidate's fields (partial update)."""
    supabase = get_supabase_admin()

    existing = (
        supabase.table("candidates")
        .select("id, created_by")
        .eq("id", str(candidate_id))
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if (
        user.role == UserRole.talent_partner
        and existing.data["created_by"] != str(user.id)
    ):
        raise HTTPException(
            status_code=403,
            detail="You can only update candidates you created",
        )

    ALLOWED_FIELDS = {
        "first_name",
        "last_name",
        "email",
        "phone",
        "location",
        "linkedin_url",
        "cv_text",
        "profile_text",
        "skills",
        "experience",
        "seniority",
        "salary_expectation",
        "availability",
        "industries",
        "extraction_flags",
    }
    update_data = {k: v for k, v in body.items() if k in ALLOWED_FIELDS}

    if not update_data:
        raise HTTPException(
            status_code=422, detail="No valid fields to update"
        )

    result = (
        supabase.table("candidates")
        .update(update_data)
        .eq("id", str(candidate_id))
        .execute()
    )

    return result.data[0] if result.data else {}
