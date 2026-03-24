from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .shared import Visibility


class CollectionCreate(BaseModel):
    name: str
    description: str | None = None
    visibility: Visibility = Visibility.private
    shared_with: list[UUID] | None = None
    tags: list[str] = []


class Collection(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    owner_id: UUID
    visibility: Visibility = Visibility.private
    shared_with: list[UUID] | None = None
    candidate_ids: list[UUID] = []
    tags: list[str] = []
    candidate_count: int = 0
    avg_match_score: float | None = None
    available_now_count: int = 0
    created_at: datetime
    updated_at: datetime
