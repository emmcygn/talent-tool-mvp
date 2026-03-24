from datetime import datetime
from uuid import UUID, uuid4

from config import settings
from contracts.match import Match
from contracts.shared import (
    AvailabilityStatus,
    ConfidenceLevel,
    ExtractedSkill,
    MatchStatus,
    RequiredSkill,
    SalaryRange,
    SeniorityLevel,
)
from matching.scorer import CompositeScorer
from matching.semantic import SemanticSearch
from matching.structured import StructuredFilter


class MatchingEngine:
    """Orchestrates the full matching pipeline: filter -> search -> score -> store."""

    def __init__(self, supabase):
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
        """Run the full matching pipeline for a role.

        1. Load role with structured requirements + embedding
        2. Structured filter: narrow candidate pool by hard requirements
        3. Semantic search: pgvector cosine similarity on filtered pool
        4. Composite scoring: 40% skill, 35% semantic, 25% experience
        5. Bucket into Strong/Good/Possible
        6. Store match results in database
        7. Return ranked matches
        """
        # 1. Load role
        role_result = (
            self.supabase.table("roles")
            .select("*")
            .eq("id", str(role_id))
            .single()
            .execute()
        )
        role_data = role_result.data

        if not role_data or not role_data.get("embedding"):
            raise ValueError(
                f"Role {role_id} not found or missing embedding"
            )

        required_skills = [
            RequiredSkill(**s)
            for s in (role_data.get("required_skills") or [])
        ]
        preferred_skills = [
            RequiredSkill(**s)
            for s in (role_data.get("preferred_skills") or [])
        ]
        role_seniority = (
            SeniorityLevel(role_data["seniority"])
            if role_data.get("seniority")
            else None
        )
        role_salary = (
            SalaryRange(**role_data["salary_band"])
            if role_data.get("salary_band")
            else None
        )
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
        semantic_results = (
            await self.semantic_search.find_similar_candidates(
                role_embedding=role_embedding,
                candidate_pool=filtered_ids,
                top_k=top_k,
            )
        )

        if not semantic_results:
            return []

        # 4. Load candidate details for scoring
        candidate_ids = [str(r["candidate_id"]) for r in semantic_results]
        candidates_result = (
            self.supabase.table("candidates")
            .select("*")
            .in_("id", candidate_ids)
            .execute()
        )
        candidates_map = {
            c["id"]: c for c in (candidates_result.data or [])
        }

        similarity_map = {
            str(r["candidate_id"]): r["similarity_score"]
            for r in semantic_results
        }

        # 5. Score each candidate
        matches: list[Match] = []
        for cid_str, candidate_data in candidates_map.items():
            similarity = similarity_map.get(cid_str, 0.0)

            c_skills = [
                ExtractedSkill(**s)
                for s in (candidate_data.get("skills") or [])
            ]
            c_seniority = (
                SeniorityLevel(candidate_data["seniority"])
                if candidate_data.get("seniority")
                else None
            )
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
                    explanation="",
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
