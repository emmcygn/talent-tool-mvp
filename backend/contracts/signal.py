from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .shared import SignalType, UserRole


class SignalCreate(BaseModel):
    event_type: SignalType
    actor_id: UUID
    actor_role: UserRole
    entity_type: str
    entity_id: UUID
    metadata: dict = {}


class Signal(BaseModel):
    id: UUID
    event_type: SignalType
    actor_id: UUID
    actor_role: UserRole
    entity_type: str
    entity_id: UUID
    metadata: dict = {}
    created_at: datetime
