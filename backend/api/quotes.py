from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import CurrentUser, get_current_user, require_role
from api.deps import get_supabase_admin
from contracts.quote import QuoteRequest
from contracts.shared import QuoteStatus, UserRole
from services.quote import QuoteService

router = APIRouter()


@router.post("")
async def generate_quote(
    data: QuoteRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Generate a placement fee quote for a candidate-role pairing.
    Calculates base fee by seniority, applies pool discount if eligible.
    """
    supabase = get_supabase_admin()
    service = QuoteService(supabase)
    try:
        result = await service.generate_quote(
            client_id=user.id,
            candidate_id=data.candidate_id,
            role_id=data.role_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("")
async def list_quotes(
    status: Optional[QuoteStatus] = None,
    limit: int = Query(default=50, le=100),
    user: CurrentUser = Depends(get_current_user),
):
    """List quotes for the current client."""
    supabase = get_supabase_admin()
    service = QuoteService(supabase)
    return await service.list_quotes_for_client(
        client_id=user.id,
        status=status,
        limit=limit,
    )


@router.get("/{quote_id}")
async def get_quote(
    quote_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    """Get a single quote with fee breakdown.

    Clients can only see their own quotes. Talent partners and admins see all.
    """
    supabase = get_supabase_admin()
    service = QuoteService(supabase)
    result = await service.get_quote(quote_id)
    if not result:
        raise HTTPException(status_code=404, detail="Quote not found")

    # Clients can only view their own quotes
    if (
        user.role == UserRole.client
        and result.get("client_id") != str(user.id)
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    return result


@router.patch("/{quote_id}/status")
async def update_quote_status(
    quote_id: UUID,
    status: QuoteStatus,
    user: CurrentUser = Depends(get_current_user),
):
    """Update quote status (accept, decline). Valid transitions are enforced.

    Clients can only update their own quotes. Admins can update any.
    """
    supabase = get_supabase_admin()

    # Check ownership for clients
    if user.role == UserRole.client:
        service = QuoteService(supabase)
        existing = await service.get_quote(quote_id)
        if not existing or existing.get("client_id") != str(user.id):
            raise HTTPException(status_code=403, detail="Access denied")
    service = QuoteService(supabase)
    result = await service.update_quote_status(
        quote_id=quote_id,
        new_status=status,
        actor_id=user.id,
        actor_role=user.role,
    )
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Invalid status transition or quote not found",
        )
    return result
