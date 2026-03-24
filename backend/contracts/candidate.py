from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .shared import (
    AvailabilityStatus,
    CandidateSource,
    ExperienceEntry,
    ExtractedSkill,
    SalaryRange,
    SeniorityLevel,
)


class CandidateCreate(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    cv_text: str | None = None
    profile_text: str | None = None


class Candidate(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    skills: list[ExtractedSkill] = []
    experience: list[ExperienceEntry] = []
    seniority: SeniorityLevel | None = None
    salary_expectation: SalaryRange | None = None
    availability: AvailabilityStatus | None = None
    industries: list[str] = []
    cv_text: str | None = None
    profile_text: str | None = None
    sources: list[CandidateSource] = []
    dedup_group: UUID | None = None
    dedup_confidence: float | None = None
    embedding: list[float] | None = None
    extraction_confidence: float | None = None
    extraction_flags: list[str] = []
    created_at: datetime
    updated_at: datetime
    created_by: UUID


class CandidateAnonymized(BaseModel):
    """Client-facing view — no full name, no company names."""

    id: UUID
    first_name: str
    last_initial: str
    location: str | None = None
    skills: list[ExtractedSkill] = []
    seniority: SeniorityLevel | None = None
    availability: AvailabilityStatus | None = None
    industries: list[str] = []
    experience_years: int | None = None
    is_pool_candidate: bool = False
