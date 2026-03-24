# Agent A — Task 09: Structured + Semantic Matching

## Mission
Build the hybrid matching engine that combines structured field filtering, pgvector cosine similarity search, and composite scoring to rank candidates against roles and bucket them into confidence tiers.

## Context
This is Day 3. The AI extraction pipeline (Task 07) has populated candidates with structured fields (skills, experience, seniority, location, availability, salary) and embeddings. Roles also have extracted requirements and embeddings. This task builds the core matching logic that powers the entire platform — structured filtering narrows the pool, semantic search finds similar profiles, and the composite scorer produces a final ranked list with confidence buckets.

## Prerequisites
- Task 07 complete (AI extraction pipeline — candidates and roles have structured fields + embeddings)
- Task 02 complete (Supabase schema with pgvector extension enabled)
- Task 03 complete (FastAPI skeleton with database connection)
- `backend/contracts/match.py` exists with `Match`, `SkillMatch`, `ConfidenceLevel` models
- `backend/contracts/shared.py` exists with `ExtractedSkill`, `RequiredSkill`, `SeniorityLevel`, `AvailabilityStatus`

## Checklist
- [ ] Create `backend/matching/__init__.py`
- [ ] Create `backend/matching/structured.py` — structured field filter
- [ ] Create `backend/matching/semantic.py` — pgvector cosine similarity search
- [ ] Create `backend/matching/scorer.py` — composite scorer with 40/35/25 weights
- [ ] Create `backend/matching/engine.py` — orchestrator that chains filter → search → score → bucket
- [ ] Create `backend/tests/test_matching.py` — unit tests for each component
- [ ] Run tests, verify pass
- [ ] Commit: "Agent A Task 09: Structured + semantic matching engine"

## Implementation Details

### Structured Filter (`backend/matching/structured.py`)

```python
from uuid import UUID
from backend.config import settings
from backend.contracts.shared import (
    SeniorityLevel, AvailabilityStatus, SalaryRange
)
from supabase import Client


SENIORITY_ORDER = {
    SeniorityLevel.junior: 1,
    SeniorityLevel.mid: 2,
    SeniorityLevel.senior: 3,
    SeniorityLevel.lead: 4,
    SeniorityLevel.principal: 5,
}

AVAILABILITY_PASSTHROUGH = {
    AvailabilityStatus.immediate,
    AvailabilityStatus.one_month,
    AvailabilityStatus.three_months,
}


class StructuredFilter:
    """Filters candidates by hard requirements: location, salary, availability, min experience."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def filter_candidates(
        self,
        role_location: str | None,
        role_salary_band: SalaryRange | None,
        role_seniority: SeniorityLevel | None,
        required_availability: list[AvailabilityStatus] | None = None,
        min_experience_years: float | None = None,
        exclude_candidate_ids: list[UUID] | None = None,
    ) -> list[UUID]:
        """
        Returns candidate IDs that pass all hard-requirement filters.
        Filters are applied additively (AND logic).
        If a filter parameter is None, that filter is skipped (permissive).
        """
        query = self.supabase.table("candidates").select("id, location, salary_expectation, seniority, availability, skills, experience")

        # Location filter: match if candidate location contains role location substring
        # or if either is None (remote/flexible)
        # We do this in Python because substring matching is easier
        result = query.execute()
        candidates = result.data

        filtered = []
        for c in candidates:
            cid = c["id"]

            # Exclude already-processed candidates
            if exclude_candidate_ids and cid in [str(eid) for eid in exclude_candidate_ids]:
                continue

            # Location filter
            if role_location and c.get("location"):
                candidate_loc = (c["location"] or "").lower()
                role_loc = role_location.lower()
                # Pass if candidate location contains role location or either mentions "remote"
                if role_loc not in candidate_loc and "remote" not in candidate_loc and "remote" not in role_loc:
                    continue

            # Salary filter: candidate expectation must overlap with role band
            if role_salary_band and c.get("salary_expectation"):
                csal = c["salary_expectation"]
                if isinstance(csal, dict):
                    c_min = float(csal.get("min_amount") or 0)
                    c_max = float(csal.get("max_amount") or 999999)
                    r_min = float(role_salary_band.min_amount or 0)
                    r_max = float(role_salary_band.max_amount or 999999)
                    # Overlap check: candidate range intersects role range
                    if c_max < r_min or c_min > r_max:
                        continue

            # Availability filter
            if required_availability and c.get("availability"):
                if c["availability"] not in [a.value for a in required_availability]:
                    continue

            # Seniority / experience filter
            if role_seniority and c.get("seniority"):
                candidate_level = SENIORITY_ORDER.get(SeniorityLevel(c["seniority"]), 0)
                required_level = SENIORITY_ORDER.get(role_seniority, 0)
                # Candidate must be at or above the required seniority level minus 1
                # (allow one level below for stretch candidates)
                if candidate_level < required_level - 1:
                    continue

            # Min experience years filter (sum of experience durations)
            if min_experience_years is not None:
                total_months = 0
                for exp in (c.get("experience") or []):
                    if isinstance(exp, dict):
                        total_months += exp.get("duration_months", 0) or 0
                total_years = total_months / 12.0
                if total_years < min_experience_years:
                    continue

            filtered.append(UUID(cid))

        return filtered
```

### Semantic Search (`backend/matching/semantic.py`)

```python
from uuid import UUID
from backend.config import settings
from supabase import Client


class SemanticSearch:
    """pgvector cosine similarity search for candidate-role matching."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def find_similar_candidates(
        self,
        role_embedding: list[float],
        candidate_pool: list[UUID] | None = None,
        top_k: int = 50,
    ) -> list[dict]:
        """
        Find top_k candidates most similar to the role embedding.

        If candidate_pool is provided, only search within those IDs.
        Returns list of {candidate_id, similarity_score} sorted by similarity desc.

        Uses pgvector's cosine distance operator (<=>).
        We call a Supabase RPC function for the vector search.
        """
        # Call the match_candidates RPC function defined in the migration
        params = {
            "query_embedding": role_embedding,
            "match_count": top_k,
        }

        if candidate_pool:
            params["candidate_ids"] = [str(cid) for cid in candidate_pool]

        result = self.supabase.rpc("match_candidates", params).execute()

        return [
            {
                "candidate_id": UUID(row["id"]),
                "similarity_score": 1.0 - row["distance"],  # cosine distance → similarity
            }
            for row in (result.data or [])
        ]


# SQL function to create in migration (add to Task 02 migration or a new one):
MATCH_CANDIDATES_SQL = """
CREATE OR REPLACE FUNCTION match_candidates(
    query_embedding vector(1536),
    match_count int DEFAULT 50,
    candidate_ids uuid[] DEFAULT NULL
)
RETURNS TABLE(id uuid, distance float)
LANGUAGE plpgsql
AS $$
BEGIN
    IF candidate_ids IS NOT NULL THEN
        RETURN QUERY
        SELECT c.id, c.embedding <=> query_embedding AS distance
        FROM candidates c
        WHERE c.embedding IS NOT NULL
          AND c.id = ANY(candidate_ids)
        ORDER BY c.embedding <=> query_embedding
        LIMIT match_count;
    ELSE
        RETURN QUERY
        SELECT c.id, c.embedding <=> query_embedding AS distance
        FROM candidates c
        WHERE c.embedding IS NOT NULL
        ORDER BY c.embedding <=> query_embedding
        LIMIT match_count;
    END IF;
END;
$$;
"""
```

### Composite Scorer (`backend/matching/scorer.py`)

```python
from backend.contracts.shared import (
    ExtractedSkill, RequiredSkill, SeniorityLevel,
    SkillMatch, ConfidenceLevel
)

# Scoring weights
WEIGHT_SKILL_OVERLAP = 0.40
WEIGHT_SEMANTIC_SIMILARITY = 0.35
WEIGHT_EXPERIENCE_FIT = 0.25

SENIORITY_ORDER = {
    SeniorityLevel.junior: 1,
    SeniorityLevel.mid: 2,
    SeniorityLevel.senior: 3,
    SeniorityLevel.lead: 4,
    SeniorityLevel.principal: 5,
}


class CompositeScorer:
    """Scores candidates against roles using weighted combination of three factors."""

    def score(
        self,
        candidate_skills: list[ExtractedSkill],
        candidate_seniority: SeniorityLevel | None,
        candidate_experience_months: int,
        role_required_skills: list[RequiredSkill],
        role_preferred_skills: list[RequiredSkill],
        role_seniority: SeniorityLevel | None,
        semantic_similarity: float,
    ) -> dict:
        """
        Compute composite score and return full breakdown.

        Returns:
            {
                "overall_score": float,         # 0-1
                "structured_score": float,      # skill overlap component (0-1)
                "semantic_score": float,         # embedding similarity (0-1)
                "experience_score": float,      # experience/seniority fit (0-1)
                "skill_overlap": list[SkillMatch],
                "confidence": ConfidenceLevel,
                "scoring_breakdown": dict,
            }
        """
        # 1. Skill overlap scoring
        skill_overlap, skill_score = self._compute_skill_overlap(
            candidate_skills, role_required_skills, role_preferred_skills
        )

        # 2. Semantic similarity (already 0-1 from pgvector)
        semantic_score = max(0.0, min(1.0, semantic_similarity))

        # 3. Experience / seniority fit
        experience_score = self._compute_experience_fit(
            candidate_seniority, role_seniority, candidate_experience_months
        )

        # 4. Composite
        overall = (
            WEIGHT_SKILL_OVERLAP * skill_score
            + WEIGHT_SEMANTIC_SIMILARITY * semantic_score
            + WEIGHT_EXPERIENCE_FIT * experience_score
        )
        overall = round(overall, 4)

        # 5. Confidence bucket
        confidence = self._bucket_confidence(overall)

        return {
            "overall_score": overall,
            "structured_score": round(skill_score, 4),
            "semantic_score": round(semantic_score, 4),
            "experience_score": round(experience_score, 4),
            "skill_overlap": skill_overlap,
            "confidence": confidence,
            "scoring_breakdown": {
                "weights": {
                    "skill_overlap": WEIGHT_SKILL_OVERLAP,
                    "semantic_similarity": WEIGHT_SEMANTIC_SIMILARITY,
                    "experience_fit": WEIGHT_EXPERIENCE_FIT,
                },
                "components": {
                    "skill_overlap_raw": round(skill_score, 4),
                    "semantic_similarity_raw": round(semantic_score, 4),
                    "experience_fit_raw": round(experience_score, 4),
                },
                "weighted_components": {
                    "skill_overlap_weighted": round(WEIGHT_SKILL_OVERLAP * skill_score, 4),
                    "semantic_similarity_weighted": round(WEIGHT_SEMANTIC_SIMILARITY * semantic_score, 4),
                    "experience_fit_weighted": round(WEIGHT_EXPERIENCE_FIT * experience_score, 4),
                },
                "overall_score": overall,
            },
        }

    def _compute_skill_overlap(
        self,
        candidate_skills: list[ExtractedSkill],
        required_skills: list[RequiredSkill],
        preferred_skills: list[RequiredSkill],
    ) -> tuple[list[SkillMatch], float]:
        """
        Compare candidate skills against required + preferred skills.
        Required skills are weighted 2x vs preferred.
        """
        # Normalize candidate skills to lowercase lookup
        c_skills = {}
        for s in candidate_skills:
            c_skills[s.name.lower().strip()] = s

        overlaps: list[SkillMatch] = []
        total_weight = 0.0
        earned_weight = 0.0

        for skill in required_skills:
            weight = 2.0  # required skills count double
            total_weight += weight
            skill_name_lower = skill.name.lower().strip()

            match = self._find_skill_match(skill_name_lower, c_skills)
            if match:
                candidate_skill = match
                # Check years requirement
                if skill.min_years and candidate_skill.years:
                    if candidate_skill.years >= skill.min_years:
                        status = "matched"
                        earned_weight += weight
                    else:
                        status = "partial"
                        ratio = candidate_skill.years / skill.min_years
                        earned_weight += weight * min(ratio, 1.0) * 0.7
                else:
                    status = "matched"
                    earned_weight += weight

                overlaps.append(SkillMatch(
                    skill_name=skill.name,
                    status=status,
                    candidate_years=candidate_skill.years,
                    required_years=skill.min_years,
                ))
            else:
                overlaps.append(SkillMatch(
                    skill_name=skill.name,
                    status="missing",
                    candidate_years=None,
                    required_years=skill.min_years,
                ))

        for skill in preferred_skills:
            weight = 1.0
            total_weight += weight
            skill_name_lower = skill.name.lower().strip()

            match = self._find_skill_match(skill_name_lower, c_skills)
            if match:
                earned_weight += weight
                overlaps.append(SkillMatch(
                    skill_name=skill.name,
                    status="matched",
                    candidate_years=match.years,
                    required_years=skill.min_years,
                ))
            else:
                overlaps.append(SkillMatch(
                    skill_name=skill.name,
                    status="missing",
                    candidate_years=None,
                    required_years=skill.min_years,
                ))

        score = (earned_weight / total_weight) if total_weight > 0 else 0.5
        return overlaps, min(score, 1.0)

    def _find_skill_match(
        self, target: str, candidate_skills: dict[str, ExtractedSkill]
    ) -> ExtractedSkill | None:
        """
        Find a matching skill in candidate's skills.
        Handles exact match and common aliases.
        """
        # Exact match
        if target in candidate_skills:
            return candidate_skills[target]

        # Common alias matching
        ALIASES = {
            "javascript": ["js", "ecmascript"],
            "typescript": ["ts"],
            "python": ["py"],
            "react": ["reactjs", "react.js"],
            "node": ["nodejs", "node.js"],
            "postgresql": ["postgres", "psql"],
            "kubernetes": ["k8s"],
            "amazon web services": ["aws"],
            "google cloud platform": ["gcp"],
            "machine learning": ["ml"],
            "artificial intelligence": ["ai"],
            "ci/cd": ["cicd", "continuous integration"],
            "docker": ["containerization"],
        }

        for canonical, aliases in ALIASES.items():
            all_names = [canonical] + aliases
            if target in all_names:
                for name in all_names:
                    if name in candidate_skills:
                        return candidate_skills[name]

        # Substring matching as fallback (e.g., "react" matches "react native")
        for skill_name, skill in candidate_skills.items():
            if target in skill_name or skill_name in target:
                return skill

        return None

    def _compute_experience_fit(
        self,
        candidate_seniority: SeniorityLevel | None,
        role_seniority: SeniorityLevel | None,
        candidate_experience_months: int,
    ) -> float:
        """
        Score how well candidate experience/seniority matches role requirements.
        Perfect match = 1.0, one level off = 0.7, two levels off = 0.3.
        """
        if not role_seniority:
            return 0.7  # neutral if role doesn't specify

        if not candidate_seniority:
            # Estimate from experience months
            years = candidate_experience_months / 12.0
            if years >= 10:
                candidate_seniority = SeniorityLevel.principal
            elif years >= 7:
                candidate_seniority = SeniorityLevel.lead
            elif years >= 4:
                candidate_seniority = SeniorityLevel.senior
            elif years >= 2:
                candidate_seniority = SeniorityLevel.mid
            else:
                candidate_seniority = SeniorityLevel.junior

        c_level = SENIORITY_ORDER.get(candidate_seniority, 2)
        r_level = SENIORITY_ORDER.get(role_seniority, 2)
        diff = abs(c_level - r_level)

        if diff == 0:
            return 1.0
        elif diff == 1:
            return 0.7
        elif diff == 2:
            return 0.3
        else:
            return 0.1

    def _bucket_confidence(self, overall_score: float) -> ConfidenceLevel:
        """Bucket overall score into confidence levels."""
        if overall_score > 0.75:
            return ConfidenceLevel.strong
        elif overall_score >= 0.5:
            return ConfidenceLevel.good
        elif overall_score >= 0.3:
            return ConfidenceLevel.possible
        else:
            return ConfidenceLevel.possible  # floor at possible, never exclude
```

### Matching Engine Orchestrator (`backend/matching/engine.py`)

```python
from uuid import UUID, uuid4
from datetime import datetime
from backend.config import settings
from backend.contracts.candidate import Candidate
from backend.contracts.role import Role
from backend.contracts.match import Match
from backend.contracts.shared import (
    ConfidenceLevel, AvailabilityStatus, MatchStatus
)
from backend.matching.structured import StructuredFilter
from backend.matching.semantic import SemanticSearch
from backend.matching.scorer import CompositeScorer
from supabase import Client


class MatchingEngine:
    """Orchestrates the full matching pipeline: filter → search → score → store."""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.structured_filter = StructuredFilter(supabase)
        self.semantic_search = SemanticSearch(supabase)
        self.scorer = CompositeScorer()

    async def run_matching(
        self,
        role_id: UUID,
        top_k: int = 50,
        min_confidence: ConfidenceLevel = ConfidenceLevel.possible,
    ) -> list[Match]:
        """
        Run the full matching pipeline for a role.

        1. Load role with structured requirements + embedding
        2. Structured filter: narrow candidate pool by hard requirements
        3. Semantic search: pgvector cosine similarity on filtered pool (top_k)
        4. Composite scoring: 40% skill, 35% semantic, 25% experience
        5. Bucket into Strong/Good/Possible
        6. Store match results in database
        7. Return ranked matches
        """
        # 1. Load role
        role_result = self.supabase.table("roles").select("*").eq("id", str(role_id)).single().execute()
        role_data = role_result.data

        if not role_data or not role_data.get("embedding"):
            raise ValueError(f"Role {role_id} not found or missing embedding")

        # Parse role fields
        from backend.contracts.shared import RequiredSkill, SeniorityLevel, SalaryRange
        required_skills = [RequiredSkill(**s) for s in (role_data.get("required_skills") or [])]
        preferred_skills = [RequiredSkill(**s) for s in (role_data.get("preferred_skills") or [])]
        role_seniority = SeniorityLevel(role_data["seniority"]) if role_data.get("seniority") else None
        role_salary = SalaryRange(**role_data["salary_band"]) if role_data.get("salary_band") else None
        role_location = role_data.get("location")
        role_embedding = role_data["embedding"]

        # 2. Structured filter
        filtered_ids = await self.structured_filter.filter_candidates(
            role_location=role_location,
            role_salary_band=role_salary,
            role_seniority=role_seniority,
            required_availability=[
                AvailabilityStatus.immediate,
                AvailabilityStatus.one_month,
                AvailabilityStatus.three_months,
            ],
        )

        if not filtered_ids:
            return []

        # 3. Semantic search within filtered pool
        semantic_results = await self.semantic_search.find_similar_candidates(
            role_embedding=role_embedding,
            candidate_pool=filtered_ids,
            top_k=top_k,
        )

        if not semantic_results:
            return []

        # 4. Load candidate details for scoring
        candidate_ids = [str(r["candidate_id"]) for r in semantic_results]
        candidates_result = self.supabase.table("candidates").select("*").in_("id", candidate_ids).execute()
        candidates_map = {c["id"]: c for c in (candidates_result.data or [])}

        # Build similarity lookup
        similarity_map = {
            str(r["candidate_id"]): r["similarity_score"]
            for r in semantic_results
        }

        # 5. Score each candidate
        matches: list[Match] = []
        from backend.contracts.shared import ExtractedSkill
        for cid_str, candidate_data in candidates_map.items():
            similarity = similarity_map.get(cid_str, 0.0)

            c_skills = [ExtractedSkill(**s) for s in (candidate_data.get("skills") or [])]
            c_seniority = SeniorityLevel(candidate_data["seniority"]) if candidate_data.get("seniority") else None
            c_exp_months = sum(
                (e.get("duration_months") or 0)
                for e in (candidate_data.get("experience") or [])
                if isinstance(e, dict)
            )

            score_result = self.scorer.score(
                candidate_skills=c_skills,
                candidate_seniority=c_seniority,
                candidate_experience_months=c_exp_months,
                role_required_skills=required_skills,
                role_preferred_skills=preferred_skills,
                role_seniority=role_seniority,
                semantic_similarity=similarity,
            )

            # Only include if meets minimum confidence
            confidence = score_result["confidence"]
            if self._confidence_meets_minimum(confidence, min_confidence):
                match = Match(
                    id=uuid4(),
                    candidate_id=UUID(cid_str),
                    role_id=role_id,
                    overall_score=score_result["overall_score"],
                    structured_score=score_result["structured_score"],
                    semantic_score=score_result["semantic_score"],
                    skill_overlap=score_result["skill_overlap"],
                    confidence=confidence,
                    explanation="",  # Populated by Task 10 explainer
                    strengths=[],
                    gaps=[],
                    recommendation="",
                    scoring_breakdown=score_result["scoring_breakdown"],
                    model_version=settings.openai_model,
                    created_at=datetime.utcnow(),
                    status=MatchStatus.generated,
                )
                matches.append(match)

        # 6. Sort by overall score descending
        matches.sort(key=lambda m: m.overall_score, reverse=True)

        # 7. Store in database
        for match in matches:
            self.supabase.table("matches").upsert(
                match.model_dump(mode="json"),
                on_conflict="candidate_id,role_id",
            ).execute()

        return matches

    def _confidence_meets_minimum(
        self, confidence: ConfidenceLevel, minimum: ConfidenceLevel
    ) -> bool:
        order = {
            ConfidenceLevel.strong: 3,
            ConfidenceLevel.good: 2,
            ConfidenceLevel.possible: 1,
        }
        return order[confidence] >= order[minimum]
```

### Migration Addition for `match_candidates` RPC

Add this to the existing migration file or create `supabase/migrations/003_match_candidates_rpc.sql`:

```sql
-- pgvector cosine similarity search function
CREATE OR REPLACE FUNCTION match_candidates(
    query_embedding vector(1536),
    match_count int DEFAULT 50,
    candidate_ids uuid[] DEFAULT NULL
)
RETURNS TABLE(id uuid, distance float)
LANGUAGE plpgsql
AS $$
BEGIN
    IF candidate_ids IS NOT NULL THEN
        RETURN QUERY
        SELECT c.id, (c.embedding <=> query_embedding)::float AS distance
        FROM candidates c
        WHERE c.embedding IS NOT NULL
          AND c.id = ANY(candidate_ids)
        ORDER BY c.embedding <=> query_embedding
        LIMIT match_count;
    ELSE
        RETURN QUERY
        SELECT c.id, (c.embedding <=> query_embedding)::float AS distance
        FROM candidates c
        WHERE c.embedding IS NOT NULL
        ORDER BY c.embedding <=> query_embedding
        LIMIT match_count;
    END IF;
END;
$$;

-- Ensure unique constraint on matches for upsert
ALTER TABLE matches ADD CONSTRAINT matches_candidate_role_unique
    UNIQUE (candidate_id, role_id);
```

### Tests (`backend/tests/test_matching.py`)

```python
import pytest
from backend.matching.scorer import CompositeScorer
from backend.contracts.shared import (
    ExtractedSkill, RequiredSkill, SeniorityLevel,
    ConfidenceLevel, SkillMatch
)


@pytest.fixture
def scorer():
    return CompositeScorer()


def test_perfect_skill_match(scorer):
    candidate_skills = [
        ExtractedSkill(name="Python", years=5),
        ExtractedSkill(name="FastAPI", years=3),
        ExtractedSkill(name="PostgreSQL", years=4),
    ]
    required = [
        RequiredSkill(name="Python", min_years=3),
        RequiredSkill(name="FastAPI", min_years=2),
    ]
    preferred = [RequiredSkill(name="PostgreSQL")]

    result = scorer.score(
        candidate_skills=candidate_skills,
        candidate_seniority=SeniorityLevel.senior,
        candidate_experience_months=60,
        role_required_skills=required,
        role_preferred_skills=preferred,
        role_seniority=SeniorityLevel.senior,
        semantic_similarity=0.85,
    )

    assert result["overall_score"] > 0.75
    assert result["confidence"] == ConfidenceLevel.strong
    matched = [s for s in result["skill_overlap"] if s.status == "matched"]
    assert len(matched) == 3


def test_partial_skill_match(scorer):
    candidate_skills = [
        ExtractedSkill(name="Python", years=2),  # below required 5 years
    ]
    required = [
        RequiredSkill(name="Python", min_years=5),
        RequiredSkill(name="Go"),  # missing
    ]
    result = scorer.score(
        candidate_skills=candidate_skills,
        candidate_seniority=SeniorityLevel.mid,
        candidate_experience_months=24,
        role_required_skills=required,
        role_preferred_skills=[],
        role_seniority=SeniorityLevel.senior,
        semantic_similarity=0.5,
    )

    assert result["overall_score"] < 0.75
    partial = [s for s in result["skill_overlap"] if s.status == "partial"]
    missing = [s for s in result["skill_overlap"] if s.status == "missing"]
    assert len(partial) == 1
    assert len(missing) == 1


def test_no_skills_required(scorer):
    result = scorer.score(
        candidate_skills=[ExtractedSkill(name="Python", years=3)],
        candidate_seniority=SeniorityLevel.mid,
        candidate_experience_months=36,
        role_required_skills=[],
        role_preferred_skills=[],
        role_seniority=SeniorityLevel.mid,
        semantic_similarity=0.7,
    )
    # With no skills to compare, skill overlap defaults to 0.5
    assert 0.3 <= result["overall_score"] <= 0.9


def test_confidence_buckets(scorer):
    # Strong: > 0.75
    result_strong = scorer.score(
        candidate_skills=[ExtractedSkill(name="Python", years=8)],
        candidate_seniority=SeniorityLevel.senior,
        candidate_experience_months=96,
        role_required_skills=[RequiredSkill(name="Python", min_years=5)],
        role_preferred_skills=[],
        role_seniority=SeniorityLevel.senior,
        semantic_similarity=0.95,
    )
    assert result_strong["confidence"] == ConfidenceLevel.strong

    # Possible: 0.3-0.5
    result_possible = scorer.score(
        candidate_skills=[],
        candidate_seniority=SeniorityLevel.junior,
        candidate_experience_months=6,
        role_required_skills=[
            RequiredSkill(name="Python", min_years=5),
            RequiredSkill(name="Go", min_years=3),
        ],
        role_preferred_skills=[],
        role_seniority=SeniorityLevel.lead,
        semantic_similarity=0.3,
    )
    assert result_possible["confidence"] == ConfidenceLevel.possible


def test_seniority_exact_match(scorer):
    result = scorer.score(
        candidate_skills=[],
        candidate_seniority=SeniorityLevel.senior,
        candidate_experience_months=60,
        role_required_skills=[],
        role_preferred_skills=[],
        role_seniority=SeniorityLevel.senior,
        semantic_similarity=0.5,
    )
    assert result["experience_score"] == 1.0


def test_seniority_one_level_off(scorer):
    result = scorer.score(
        candidate_skills=[],
        candidate_seniority=SeniorityLevel.mid,
        candidate_experience_months=36,
        role_required_skills=[],
        role_preferred_skills=[],
        role_seniority=SeniorityLevel.senior,
        semantic_similarity=0.5,
    )
    assert result["experience_score"] == 0.7


def test_alias_matching(scorer):
    candidate_skills = [ExtractedSkill(name="JS", years=5)]
    required = [RequiredSkill(name="JavaScript")]
    result = scorer.score(
        candidate_skills=candidate_skills,
        candidate_seniority=SeniorityLevel.mid,
        candidate_experience_months=36,
        role_required_skills=required,
        role_preferred_skills=[],
        role_seniority=SeniorityLevel.mid,
        semantic_similarity=0.6,
    )
    matched = [s for s in result["skill_overlap"] if s.status == "matched"]
    assert len(matched) == 1


def test_scoring_breakdown_present(scorer):
    result = scorer.score(
        candidate_skills=[ExtractedSkill(name="Python", years=3)],
        candidate_seniority=SeniorityLevel.mid,
        candidate_experience_months=36,
        role_required_skills=[RequiredSkill(name="Python")],
        role_preferred_skills=[],
        role_seniority=SeniorityLevel.mid,
        semantic_similarity=0.7,
    )
    breakdown = result["scoring_breakdown"]
    assert "weights" in breakdown
    assert breakdown["weights"]["skill_overlap"] == 0.40
    assert breakdown["weights"]["semantic_similarity"] == 0.35
    assert breakdown["weights"]["experience_fit"] == 0.25
    assert "components" in breakdown
    assert "weighted_components" in breakdown
```

## Outputs
- `backend/matching/__init__.py`
- `backend/matching/structured.py`
- `backend/matching/semantic.py`
- `backend/matching/scorer.py`
- `backend/matching/engine.py`
- `backend/tests/test_matching.py`
- `supabase/migrations/003_match_candidates_rpc.sql`

## Acceptance Criteria
1. `CompositeScorer` unit tests all pass: `python -m pytest tests/test_matching.py -v`
2. Skill alias matching resolves common technology name variations (JS/JavaScript, K8s/Kubernetes, etc.)
3. Confidence buckets are correct: Strong >0.75, Good 0.5-0.75, Possible 0.3-0.5
4. Scoring weights sum to 1.0 (0.40 + 0.35 + 0.25)
5. Full scoring breakdown is stored with every match for traceability
6. `match_candidates` RPC function works with pgvector cosine distance
7. Engine orchestrator chains filter → search → score → store correctly
8. Matches are upserted (re-running matching for the same role updates rather than duplicates)

## Handoff Notes
- **To Task 10:** Matches are stored with empty `explanation`, `strengths`, `gaps`, `recommendation`. The explainer should update these fields for Strong + Good matches.
- **To Task 11:** Match results are in the `matches` table. Provide endpoints to query by role_id and candidate_id, plus status updates.
- **To Agent B:** Match results include `skill_overlap` as a list of `SkillMatch` objects with status "matched"/"partial"/"missing" — use these for the green/amber/grey skill chips. `scoring_breakdown` has the full traceability data for the expanded card view. `confidence` maps to Strong/Good/Possible badges.
- **Decision:** Candidates below 0.3 overall score are excluded from results entirely (not stored). One level below required seniority is still allowed (stretch candidates).
