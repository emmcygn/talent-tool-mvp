import logging
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel

from api.auth import CurrentUser, get_current_user, require_role
from api.deps import PaginatedResponse, get_supabase_admin
from contracts.role import RoleCreate
from contracts.shared import (
    RemotePolicy,
    RoleStatus,
    SeniorityLevel,
    UserRole,
)
from pipelines.enrich import ExtractionPipeline

logger = logging.getLogger("recruittech.api.roles")
router = APIRouter()

extraction_pipeline = ExtractionPipeline()


@router.get("", response_model=PaginatedResponse)
async def list_roles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[RoleStatus] = None,
    organisation_id: Optional[UUID] = None,
    seniority: Optional[SeniorityLevel] = None,
    remote_policy: Optional[RemotePolicy] = None,
    user: CurrentUser = Depends(get_current_user),
):
    """List roles with optional filters."""
    supabase = get_supabase_admin()
    offset = (page - 1) * page_size

    query = supabase.table("roles").select("*", count="exact")

    if user.role == UserRole.client:
        query = query.eq("created_by", str(user.id))

    if status:
        query = query.eq("status", status.value)
    if organisation_id:
        query = query.eq("organisation_id", str(organisation_id))
    if seniority:
        query = query.eq("seniority", seniority.value)
    if remote_policy:
        query = query.eq("remote_policy", remote_policy.value)

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


@router.get("/{role_id}")
async def get_role(
    role_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    """Get a single role by ID."""
    supabase = get_supabase_admin()

    result = (
        supabase.table("roles")
        .select("*")
        .eq("id", str(role_id))
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Role not found")

    role = result.data

    if user.role == UserRole.client and role["created_by"] != str(user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    return role


@router.post("", status_code=201)
async def create_role(
    body: RoleCreate,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(
        require_role(UserRole.client, UserRole.admin)
    ),
):
    """Create a new role. Triggers requirement extraction in background."""
    supabase = get_supabase_admin()

    role_id = uuid4()
    record = {
        "id": str(role_id),
        "title": body.title,
        "description": body.description,
        "organisation_id": str(body.organisation_id),
        "salary_band": (
            body.salary_band.model_dump(mode="json")
            if body.salary_band
            else None
        ),
        "location": body.location,
        "remote_policy": body.remote_policy.value,
        "required_skills": [],
        "preferred_skills": [],
        "status": RoleStatus.draft.value,
        "created_by": str(user.id),
    }

    result = supabase.table("roles").insert(record).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create role")

    created = result.data[0]

    background_tasks.add_task(_run_role_extraction, role_id)

    return created


async def _run_role_extraction(role_id: UUID):
    """Background task: extract requirements from role description."""
    try:
        logger.info(f"Running requirement extraction for role {role_id}")
        await extraction_pipeline.extract_role(role_id)

        supabase = get_supabase_admin()
        supabase.table("roles").update(
            {"status": RoleStatus.active.value}
        ).eq("id", str(role_id)).execute()

        logger.info(f"Role {role_id} extracted and activated")
    except Exception as e:
        logger.error(f"Role extraction failed for {role_id}: {e}")


@router.patch("/{role_id}")
async def update_role(
    role_id: UUID,
    body: dict,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(get_current_user),
):
    """Update a role's fields. Re-triggers extraction if description changes."""
    supabase = get_supabase_admin()

    existing = (
        supabase.table("roles")
        .select("id, created_by")
        .eq("id", str(role_id))
        .single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="Role not found")

    # Only the role creator or an admin can update
    if (
        user.role != UserRole.admin
        and existing.data["created_by"] != str(user.id)
    ):
        raise HTTPException(
            status_code=403, detail="You can only update your own roles"
        )

    ALLOWED_FIELDS = {
        "title",
        "description",
        "salary_band",
        "location",
        "remote_policy",
        "status",
        "required_skills",
        "preferred_skills",
        "seniority",
        "industry",
    }
    update_data = {k: v for k, v in body.items() if k in ALLOWED_FIELDS}

    if not update_data:
        raise HTTPException(
            status_code=422, detail="No valid fields to update"
        )

    result = (
        supabase.table("roles")
        .update(update_data)
        .eq("id", str(role_id))
        .execute()
    )

    if "description" in update_data:
        background_tasks.add_task(_run_role_extraction, role_id)

    return result.data[0] if result.data else {}


class ExtractRequirementsRequest(BaseModel):
    description: str


@router.post("/extract-requirements")
async def extract_requirements(
    body: ExtractRequirementsRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Extract role requirements from a description using AI.

    Returns structured skills, seniority, etc. without creating a role.
    Used by the role creation wizard for preview.
    """
    pipeline = extraction_pipeline
    extraction = await pipeline._call_extraction_llm(
        body.description,
        "You are a recruitment data extraction system. Extract structured job requirements from the following role description.\n\nReturn a JSON object with exactly these fields:\n\n{\n  \"required_skills\": [{\"name\": \"skill name\", \"min_years\": years_or_null, \"importance\": \"required\"}],\n  \"preferred_skills\": [{\"name\": \"skill name\", \"min_years\": years_or_null, \"importance\": \"preferred\"}],\n  \"seniority\": \"junior|mid|senior|lead|principal\",\n  \"salary_band\": {\"min_amount\": number_or_null, \"max_amount\": number_or_null, \"currency\": \"GBP\"},\n  \"industry\": \"industry name or null\",\n  \"field_confidences\": {\"required_skills\": 0.0_to_1.0, \"preferred_skills\": 0.0_to_1.0, \"seniority\": 0.0_to_1.0, \"salary_band\": 0.0_to_1.0, \"industry\": 0.0_to_1.0}\n}\n\nRules:\n- Distinguish required vs preferred skills based on language\n- UK market context — GBP for salary\n- Return valid JSON only",
    )
    parsed = pipeline._parse_role_extraction(extraction)
    return {
        "required_skills": parsed.required_skills,
        "preferred_skills": parsed.preferred_skills,
        "seniority": parsed.seniority.value if parsed.seniority else None,
    }
