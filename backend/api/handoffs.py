from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.auth import CurrentUser, get_current_user, require_role
from api.deps import get_supabase_admin
from contracts.handoff import HandoffCreate
from contracts.shared import HandoffStatus, UserRole
from services.handoff import HandoffService

router = APIRouter()


@router.post("")
async def create_handoff(
    data: HandoffCreate,
    user: CurrentUser = Depends(require_role(UserRole.talent_partner, UserRole.admin)),
):
    """Create a new handoff (refer candidates to another partner)."""
    supabase = get_supabase_admin()
    service = HandoffService(supabase)
    result = await service.create_handoff(
        from_partner_id=user.id,
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
    user: CurrentUser = Depends(require_role(UserRole.talent_partner, UserRole.admin)),
):
    """List handoffs received by the current partner (inbox)."""
    supabase = get_supabase_admin()
    service = HandoffService(supabase)
    return await service.list_inbox(
        partner_id=user.id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/outbox")
async def list_outbox(
    status: Optional[HandoffStatus] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(require_role(UserRole.talent_partner, UserRole.admin)),
):
    """List handoffs sent by the current partner (outbox)."""
    supabase = get_supabase_admin()
    service = HandoffService(supabase)
    return await service.list_outbox(
        partner_id=user.id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/attribution/{attribution_id}")
async def get_attribution_chain(
    attribution_id: UUID,
    user: CurrentUser = Depends(require_role(UserRole.talent_partner, UserRole.admin)),
):
    """Get the full attribution chain for a referral (all handoffs linked by attribution ID)."""
    supabase = get_supabase_admin()
    service = HandoffService(supabase)
    return await service.get_attribution_chain(attribution_id)


class HandoffResponse(BaseModel):
    accept: bool
    notes: str | None = None


@router.post("/{handoff_id}/respond")
async def respond_to_handoff(
    handoff_id: UUID,
    body: HandoffResponse,
    user: CurrentUser = Depends(require_role(UserRole.talent_partner, UserRole.admin)),
):
    """Accept or decline a handoff. Only the recipient can respond."""
    supabase = get_supabase_admin()
    service = HandoffService(supabase)
    result = await service.respond(
        handoff_id=handoff_id,
        partner_id=user.id,
        accept=body.accept,
        response_notes=body.notes,
    )
    if not result:
        raise HTTPException(
            status_code=403,
            detail="Cannot respond: not the recipient, handoff not found, or already responded",
        )
    return result


@router.get("/{handoff_id}")
async def get_handoff(
    handoff_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    """Get a single handoff with full details."""
    supabase = get_supabase_admin()
    service = HandoffService(supabase)
    result = await service.get_handoff(handoff_id)
    if not result:
        raise HTTPException(status_code=404, detail="Handoff not found")
    return result
