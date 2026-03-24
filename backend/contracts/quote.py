from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from .shared import QuoteStatus


class QuoteRequest(BaseModel):
    candidate_id: UUID
    role_id: UUID


class Quote(BaseModel):
    id: UUID
    client_id: UUID
    candidate_id: UUID
    role_id: UUID
    is_pool_candidate: bool
    base_fee: Decimal
    pool_discount: Decimal | None = None
    final_fee: Decimal
    fee_breakdown: dict = {}
    status: QuoteStatus = QuoteStatus.generated
    created_at: datetime
    expires_at: datetime
