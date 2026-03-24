import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.auth import CurrentUser, get_current_user, require_role
from api.deps import get_supabase_admin
from contracts.collection import CollectionCreate
from contracts.shared import UserRole


class AddCandidatesRequest(BaseModel):
    """Accepts either a single candidate_id or a list of candidate_ids."""

    candidate_id: UUID | None = None
    candidate_ids: list[UUID] | None = None

    def get_ids(self) -> list[UUID]:
        ids = list(self.candidate_ids or [])
        if self.candidate_id:
            ids.append(self.candidate_id)
        return ids
from services.collection import CollectionService

logger = logging.getLogger("recruittech.api.collections")
router = APIRouter()


async def _verify_collection_access(
    supabase, collection_id: UUID, user: CurrentUser, require_owner: bool = False
) -> dict:
    """Verify user can access a collection. Returns collection data.

    - Admins: always allowed
    - Owners: always allowed
    - Shared access: allowed for read (not for mutations)
    - require_owner=True: only owner or admin can proceed
    """
    service = CollectionService(supabase)
    collection = await service.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if user.role == UserRole.admin:
        return collection

    is_owner = collection.get("owner_id") == str(user.id)

    if require_owner and not is_owner:
        raise HTTPException(
            status_code=403,
            detail="Only the collection owner can perform this action",
        )

    if is_owner:
        return collection

    # Check shared access for reads
    visibility = collection.get("visibility", "private")
    if visibility == "shared_all":
        return collection
    if visibility == "shared_specific":
        shared_with = collection.get("shared_with") or []
        if str(user.id) in shared_with:
            return collection

    raise HTTPException(status_code=403, detail="Access denied")


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
    return await _verify_collection_access(supabase, collection_id, user)


@router.post("/{collection_id}/candidates")
async def add_candidates(
    collection_id: UUID,
    body: AddCandidatesRequest,
    user: CurrentUser = Depends(
        require_role(UserRole.talent_partner, UserRole.admin)
    ),
):
    """Add candidates to a collection. Accepts { candidate_id } or { candidate_ids: [...] }."""
    ids = body.get_ids()
    if not ids:
        raise HTTPException(status_code=422, detail="No candidate IDs provided")
    supabase = get_supabase_admin()
    await _verify_collection_access(
        supabase, collection_id, user, require_owner=True
    )
    service = CollectionService(supabase)
    return await service.add_candidates(collection_id, ids)


@router.delete("/{collection_id}/candidates/{candidate_id}")
async def remove_candidate(
    collection_id: UUID,
    candidate_id: UUID,
    user: CurrentUser = Depends(
        require_role(UserRole.talent_partner, UserRole.admin)
    ),
):
    """Remove a single candidate from a collection. Only the owner or admin can mutate."""
    supabase = get_supabase_admin()
    await _verify_collection_access(
        supabase, collection_id, user, require_owner=True
    )
    service = CollectionService(supabase)
    return await service.remove_candidates(collection_id, [candidate_id])


@router.delete("/{collection_id}/candidates")
async def remove_candidates_bulk(
    collection_id: UUID,
    candidate_ids: list[UUID],
    user: CurrentUser = Depends(
        require_role(UserRole.talent_partner, UserRole.admin)
    ),
):
    """Remove multiple candidates from a collection. Only the owner or admin can mutate."""
    supabase = get_supabase_admin()
    await _verify_collection_access(
        supabase, collection_id, user, require_owner=True
    )
    service = CollectionService(supabase)
    return await service.remove_candidates(collection_id, candidate_ids)


@router.get("/{collection_id}/stats")
async def get_collection_stats(
    collection_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    """Get computed stats for a collection."""
    supabase = get_supabase_admin()
    await _verify_collection_access(supabase, collection_id, user)
    service = CollectionService(supabase)
    return await service.recompute_stats(collection_id)
