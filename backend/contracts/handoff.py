from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .shared import HandoffStatus


class HandoffCreate(BaseModel):
    to_partner_id: UUID
    candidate_ids: list[UUID]
    context_notes: str
    target_role_id: UUID | None = None


class Handoff(BaseModel):
    id: UUID
    from_partner_id: UUID
    to_partner_id: UUID
    candidate_ids: list[UUID]
    context_notes: str
    target_role_id: UUID | None = None
    status: HandoffStatus = HandoffStatus.pending
    response_notes: str | None = None
    attribution_id: UUID
    created_at: datetime
    responded_at: datetime | None = None
