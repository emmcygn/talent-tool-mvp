from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .shared import ConfidenceLevel, MatchStatus, SkillMatch


class Match(BaseModel):
    id: UUID
    candidate_id: UUID
    role_id: UUID
    overall_score: float
    structured_score: float
    semantic_score: float
    skill_overlap: list[SkillMatch] = []
    confidence: ConfidenceLevel
    explanation: str
    strengths: list[str] = []
    gaps: list[str] = []
    recommendation: str
    scoring_breakdown: dict = {}
    model_version: str = ""
    created_at: datetime
    status: MatchStatus = MatchStatus.generated
