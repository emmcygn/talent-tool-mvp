from enum import Enum
from decimal import Decimal

from pydantic import BaseModel


class SeniorityLevel(str, Enum):
    junior = "junior"
    mid = "mid"
    senior = "senior"
    lead = "lead"
    principal = "principal"


class AvailabilityStatus(str, Enum):
    immediate = "immediate"
    one_month = "1_month"
    three_months = "3_months"
    not_looking = "not_looking"


class RemotePolicy(str, Enum):
    onsite = "onsite"
    hybrid = "hybrid"
    remote = "remote"


class RoleStatus(str, Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    filled = "filled"
    closed = "closed"


class MatchStatus(str, Enum):
    generated = "generated"
    shortlisted = "shortlisted"
    dismissed = "dismissed"
    intro_requested = "intro_requested"


class ConfidenceLevel(str, Enum):
    strong = "strong"
    good = "good"
    possible = "possible"


class HandoffStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    expired = "expired"


class QuoteStatus(str, Enum):
    generated = "generated"
    sent = "sent"
    accepted = "accepted"
    declined = "declined"
    expired = "expired"


class Visibility(str, Enum):
    private = "private"
    shared_specific = "shared_specific"
    shared_all = "shared_all"


class UserRole(str, Enum):
    talent_partner = "talent_partner"
    client = "client"
    admin = "admin"


class SignalType(str, Enum):
    candidate_ingested = "candidate_ingested"
    candidate_viewed = "candidate_viewed"
    candidate_shortlisted = "candidate_shortlisted"
    candidate_dismissed = "candidate_dismissed"
    match_generated = "match_generated"
    intro_requested = "intro_requested"
    handoff_sent = "handoff_sent"
    handoff_accepted = "handoff_accepted"
    handoff_declined = "handoff_declined"
    quote_generated = "quote_generated"
    placement_made = "placement_made"
    copilot_query = "copilot_query"


class ExtractedSkill(BaseModel):
    name: str
    years: float | None = None
    confidence: float = 1.0


class RequiredSkill(BaseModel):
    name: str
    min_years: float | None = None
    importance: str = "required"  # required | preferred


class ExperienceEntry(BaseModel):
    company: str
    title: str
    duration_months: int | None = None
    industry: str | None = None


class SalaryRange(BaseModel):
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    currency: str = "GBP"


class SkillMatch(BaseModel):
    skill_name: str
    status: str  # matched | partial | missing
    candidate_years: float | None = None
    required_years: float | None = None


class CandidateSource(BaseModel):
    adapter_name: str
    external_id: str
    ingested_at: str  # ISO datetime string
