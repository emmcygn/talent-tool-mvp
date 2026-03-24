import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import CurrentUser, get_current_user, require_role
from api.deps import get_supabase_admin
from contracts.collection import CollectionCreate
from contracts.shared import UserRole, Visibility
from services.collection import CollectionService

logger = logging.getLogger("recruittech.api.collections")
router = APIRouter()


@router.post("", status_code=201)
async def create_collection(
    data: CollectionCreate,
    user: CurrentUser = Depends(
        require_role(UserRole.talent_partner, UserRole.admin)
    ),
):
    """Create a new collection."""
    supabase = get_supabase_admin()
    service = CollectionService(supabase)
    result = await service.create_collection(data, owner_id=user.id)
    if not result:
        raise HTTPException(
            status_code=500, detail="Failed to create collection"
        )
    return result


@router.get("")
async def list_collections(
    include_shared: bool = Query(default=True),
    user: CurrentUser = Depends(get_current_user),
):
    """List collections visible to the current user."""
    supabase = get_supabase_admin()
    service = CollectionService(supabase)
    return await service.list_collections(
        user_id=user.id,
        user_role=user.role.value,
        include_shared=include_shared,
    )


@router.get("/{collection_id}")
async def get_collection(
    collection_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    """Get a single collection with candidate IDs and stats."""
    supabase = get_supabase_admin()
    service = CollectionService(supabase)
    result = await service.get_collection(collection_id)
    if not result:
        raise HTTPException(status_code=404, detail="Collection not found")
    return result


@router.post("/{collection_id}/candidates")
async def add_candidates(
    collection_id: UUID,
    candidate_ids: list[UUID],
    user: CurrentUser = Depends(
        require_role(UserRole.talent_partner, UserRole.admin)
    ),
):
    """Add candidates to a collection."""
    supabase = get_supabase_admin()
    service = CollectionService(supabase)
    return await service.add_candidates(collection_id, candidate_ids)


@router.delete("/{collection_id}/candidates")
async def remove_candidates(
    collection_id: UUID,
    candidate_ids: list[UUID],
    user: CurrentUser = Depends(
        require_role(UserRole.talent_partner, UserRole.admin)
    ),
):
    """Remove candidates from a collection."""
    supabase = get_supabase_admin()
    service = CollectionService(supabase)
    return await service.remove_candidates(collection_id, candidate_ids)


@router.get("/{collection_id}/stats")
async def get_collection_stats(
    collection_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    """Get computed stats for a collection."""
    supabase = get_supabase_admin()
    service = CollectionService(supabase)
    return await service.recompute_stats(collection_id)
