from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .shared import (
    RemotePolicy,
    RequiredSkill,
    RoleStatus,
    SalaryRange,
    SeniorityLevel,
)


class RoleCreate(BaseModel):
    title: str
    description: str
    organisation_id: UUID
    salary_band: SalaryRange | None = None
    location: str | None = None
    remote_policy: RemotePolicy = RemotePolicy.hybrid


class Role(BaseModel):
    id: UUID
    title: str
    description: str
    organisation_id: UUID
    required_skills: list[RequiredSkill] = []
    preferred_skills: list[RequiredSkill] = []
    seniority: SeniorityLevel | None = None
    salary_band: SalaryRange | None = None
    location: str | None = None
    remote_policy: RemotePolicy = RemotePolicy.hybrid
    industry: str | None = None
    embedding: list[float] | None = None
    extraction_confidence: float | None = None
    status: RoleStatus = RoleStatus.draft
    created_at: datetime
    created_by: UUID
