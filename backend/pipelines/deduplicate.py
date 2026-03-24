import logging
import math
import re
from datetime import datetime
from uuid import UUID, uuid4

from Levenshtein import ratio as levenshtein_ratio
from pydantic import BaseModel

from api.deps import get_supabase_admin
from contracts.shared import SignalType, UserRole

logger = logging.getLogger("recruittech.pipelines.deduplicate")


class DedupMatch(BaseModel):
    """A potential duplicate match between two candidate records."""

    candidate_id: UUID
    existing_candidate_id: UUID
    confidence: float
    match_strategies: list[str]
    details: dict = {}


class DedupDecision(BaseModel):
    """The decision made for a dedup match."""

    match: DedupMatch
    action: str  # "auto_merged", "queued_for_review", "no_match"
    merged_candidate_id: UUID | None = None


class DedupResult(BaseModel):
    """Summary of a deduplication run."""

    total_candidates_checked: int
    total_matches_found: int
    auto_merged: int
    queued_for_review: int
    no_match: int
    decisions: list[DedupDecision] = []


class DeduplicationPipeline:
    """Identity resolution pipeline with three matching strategies.

    Strategy 1: Exact match on email or phone number
    Strategy 2: Fuzzy match on name + employer (Levenshtein)
    Strategy 3: Semantic match on embedding similarity

    Confidence tiers:
    - > 0.9: auto-merge
    - 0.6 - 0.9: queue for human review
    - < 0.6: no match
    """

    AUTO_MERGE_THRESHOLD = 0.9
    REVIEW_THRESHOLD = 0.6
    EXACT_MATCH_CONFIDENCE = 0.95
    FUZZY_NAME_THRESHOLD = 0.85
    FUZZY_EMPLOYER_THRESHOLD = 0.80
    SEMANTIC_THRESHOLD = 0.95

    async def run(
        self,
        candidate_ids: list[UUID] | None = None,
    ) -> DedupResult:
        """Run deduplication on specified candidates or all un-deduped candidates."""
        supabase = get_supabase_admin()

        if candidate_ids:
            query = supabase.table("candidates").select("*").in_(
                "id", [str(cid) for cid in candidate_ids]
            )
        else:
            query = supabase.table("candidates").select("*").is_(
                "dedup_group", "null"
            )

        result = query.execute()
        new_candidates = result.data or []

        all_result = (
            supabase.table("candidates")
            .select(
                "id, first_name, last_name, email, phone, experience, embedding, sources"
            )
            .execute()
        )
        existing_candidates = all_result.data or []

        decisions: list[DedupDecision] = []
        auto_merged = 0
        queued = 0
        no_match_count = 0

        for candidate in new_candidates:
            candidate_id = UUID(candidate["id"])

            best_match = await self._find_best_match(
                candidate, existing_candidates
            )

            if best_match is None:
                no_match_count += 1
                group_id = uuid4()
                await self._set_dedup_group(
                    supabase, candidate_id, group_id, confidence=1.0
                )
                continue

            if best_match.confidence >= self.AUTO_MERGE_THRESHOLD:
                merged_id = await self._merge_candidates(
                    supabase,
                    candidate_id,
                    best_match.existing_candidate_id,
                )
                decisions.append(
                    DedupDecision(
                        match=best_match,
                        action="auto_merged",
                        merged_candidate_id=merged_id,
                    )
                )
                auto_merged += 1
                logger.info(
                    f"Auto-merged {candidate_id} into "
                    f"{best_match.existing_candidate_id} "
                    f"(confidence: {best_match.confidence:.2f})"
                )

            elif best_match.confidence >= self.REVIEW_THRESHOLD:
                await self._queue_for_review(supabase, best_match)
                decisions.append(
                    DedupDecision(
                        match=best_match,
                        action="queued_for_review",
                    )
                )
                queued += 1
                logger.info(
                    f"Queued for review: {candidate_id} vs "
                    f"{best_match.existing_candidate_id} "
                    f"(confidence: {best_match.confidence:.2f})"
                )

            else:
                no_match_count += 1
                group_id = uuid4()
                await self._set_dedup_group(
                    supabase, candidate_id, group_id, confidence=1.0
                )

        return DedupResult(
            total_candidates_checked=len(new_candidates),
            total_matches_found=len(decisions),
            auto_merged=auto_merged,
            queued_for_review=queued,
            no_match=no_match_count,
            decisions=decisions,
        )

    async def _find_best_match(
        self,
        candidate: dict,
        existing_candidates: list[dict],
    ) -> DedupMatch | None:
        """Find the best matching existing candidate across all strategies."""
        candidate_id = UUID(candidate["id"])
        best_match: DedupMatch | None = None
        best_confidence = 0.0

        for existing in existing_candidates:
            existing_id = UUID(existing["id"])
            if existing_id == candidate_id:
                continue

            confidence, strategies, details = self._compute_match_confidence(
                candidate, existing
            )

            if (
                confidence > best_confidence
                and confidence >= self.REVIEW_THRESHOLD
            ):
                best_confidence = confidence
                best_match = DedupMatch(
                    candidate_id=candidate_id,
                    existing_candidate_id=existing_id,
                    confidence=confidence,
                    match_strategies=strategies,
                    details=details,
                )

        return best_match

    def _compute_match_confidence(
        self,
        candidate: dict,
        existing: dict,
    ) -> tuple[float, list[str], dict]:
        """Compute combined match confidence from all strategies."""
        strategies: list[str] = []
        details: dict = {}
        confidences: list[float] = []

        # Strategy 1: Exact email match
        email_conf = self._exact_email_match(candidate, existing)
        if email_conf > 0:
            strategies.append("exact_email")
            confidences.append(email_conf)
            details["email_match"] = True

        # Strategy 1b: Exact phone match
        phone_conf = self._exact_phone_match(candidate, existing)
        if phone_conf > 0:
            strategies.append("exact_phone")
            confidences.append(phone_conf)
            details["phone_match"] = True

        # Strategy 2: Fuzzy name + employer match
        fuzzy_conf, fuzzy_details = self._fuzzy_match(candidate, existing)
        if fuzzy_conf > 0:
            strategies.append("fuzzy_name_employer")
            confidences.append(fuzzy_conf)
            details.update(fuzzy_details)

        # Strategy 3: Semantic embedding match
        semantic_conf = self._semantic_match(candidate, existing)
        if semantic_conf > 0:
            strategies.append("semantic_embedding")
            confidences.append(semantic_conf)
            details["semantic_similarity"] = semantic_conf

        if not confidences:
            return 0.0, [], {}

        # Combined: take max, boost if multiple strategies agree
        max_conf = max(confidences)
        if len(strategies) >= 2:
            max_conf = min(1.0, max_conf + 0.05 * (len(strategies) - 1))

        return round(max_conf, 3), strategies, details

    def _exact_email_match(self, candidate: dict, existing: dict) -> float:
        """Exact email match -> high confidence."""
        c_email = (candidate.get("email") or "").lower().strip()
        e_email = (existing.get("email") or "").lower().strip()
        if c_email and e_email and c_email == e_email:
            return self.EXACT_MATCH_CONFIDENCE
        return 0.0

    def _exact_phone_match(self, candidate: dict, existing: dict) -> float:
        """Exact phone match (normalized) -> high confidence."""

        def normalize_phone(p: str | None) -> str:
            if not p:
                return ""
            return re.sub(r"[\s\-\(\)\+]", "", p)

        c_phone = normalize_phone(candidate.get("phone"))
        e_phone = normalize_phone(existing.get("phone"))
        if c_phone and e_phone and c_phone == e_phone:
            return self.EXACT_MATCH_CONFIDENCE
        return 0.0

    def _fuzzy_match(
        self,
        candidate: dict,
        existing: dict,
    ) -> tuple[float, dict]:
        """Fuzzy match on name + employer using Levenshtein distance."""
        details = {}

        c_name = f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}".lower().strip()
        e_name = f"{existing.get('first_name', '')} {existing.get('last_name', '')}".lower().strip()

        if not c_name or not e_name:
            return 0.0, details

        name_ratio = levenshtein_ratio(c_name, e_name)
        details["name_similarity"] = round(name_ratio, 3)

        if name_ratio < self.FUZZY_NAME_THRESHOLD:
            return 0.0, details

        c_employer = self._get_current_employer(candidate)
        e_employer = self._get_current_employer(existing)

        if c_employer and e_employer:
            employer_ratio = levenshtein_ratio(
                c_employer.lower(), e_employer.lower()
            )
            details["employer_similarity"] = round(employer_ratio, 3)

            if employer_ratio >= self.FUZZY_EMPLOYER_THRESHOLD:
                combined = (name_ratio * 0.6) + (employer_ratio * 0.4)
                return round(min(combined, 0.88), 3), details

        # Name match only — lower confidence
        if name_ratio >= 0.95:
            return round(name_ratio * 0.7, 3), details

        return 0.0, details

    def _semantic_match(self, candidate: dict, existing: dict) -> float:
        """Semantic match using embedding cosine similarity."""
        c_embedding = candidate.get("embedding")
        e_embedding = existing.get("embedding")

        if not c_embedding or not e_embedding:
            return 0.0

        similarity = self._cosine_similarity(c_embedding, e_embedding)
        if similarity >= self.SEMANTIC_THRESHOLD:
            return round(similarity, 3)

        return 0.0

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    @staticmethod
    def _get_current_employer(candidate: dict) -> str | None:
        """Extract current employer from experience entries."""
        experience = candidate.get("experience", [])
        if isinstance(experience, list) and experience:
            return experience[0].get("company")
        return None

    async def _merge_candidates(
        self,
        supabase,
        incoming_id: UUID,
        existing_id: UUID,
    ) -> UUID:
        """Merge incoming candidate into existing candidate."""
        incoming = (
            supabase.table("candidates")
            .select("*")
            .eq("id", str(incoming_id))
            .single()
            .execute()
            .data
        )
        existing = (
            supabase.table("candidates")
            .select("*")
            .eq("id", str(existing_id))
            .single()
            .execute()
            .data
        )

        merged = {}
        merge_fields = [
            "email",
            "phone",
            "location",
            "linkedin_url",
            "cv_text",
            "profile_text",
            "seniority",
            "salary_expectation",
            "availability",
        ]
        for field in merge_fields:
            merged[field] = _pick_best_field(
                existing.get(field), incoming.get(field)
            )

        merged_skills = _merge_skills(
            existing.get("skills", []),
            incoming.get("skills", []),
        )
        merged_experience = _merge_experience(
            existing.get("experience", []),
            incoming.get("experience", []),
        )
        merged_sources = existing.get("sources", []) + incoming.get(
            "sources", []
        )
        merged_industries = list(
            set(
                existing.get("industries", [])
                + incoming.get("industries", [])
            )
        )

        existing_conf = existing.get("extraction_confidence") or 0.0
        incoming_conf = incoming.get("extraction_confidence") or 0.0
        best_conf = max(existing_conf, incoming_conf)

        merged_embedding = existing.get("embedding") or incoming.get(
            "embedding"
        )
        group_id = existing.get("dedup_group") or str(uuid4())

        update_data = {
            **merged,
            "skills": merged_skills,
            "experience": merged_experience,
            "sources": merged_sources,
            "industries": merged_industries,
            "extraction_confidence": best_conf if best_conf > 0 else None,
            "embedding": merged_embedding,
            "dedup_group": group_id,
            "dedup_confidence": 1.0,
        }
        supabase.table("candidates").update(update_data).eq(
            "id", str(existing_id)
        ).execute()

        supabase.table("candidates").update(
            {
                "dedup_group": group_id,
                "dedup_confidence": 0.0,
            }
        ).eq("id", str(incoming_id)).execute()

        return existing_id

    async def _set_dedup_group(
        self,
        supabase,
        candidate_id: UUID,
        group_id: UUID,
        confidence: float,
    ) -> None:
        """Set dedup_group on a candidate."""
        supabase.table("candidates").update(
            {
                "dedup_group": str(group_id),
                "dedup_confidence": confidence,
            }
        ).eq("id", str(candidate_id)).execute()

    async def _queue_for_review(
        self,
        supabase,
        match: DedupMatch,
    ) -> None:
        """Add a potential duplicate to the review queue."""
        signal = {
            "id": str(uuid4()),
            "event_type": "candidate_ingested",
            "actor_id": str(match.candidate_id),
            "actor_role": "admin",
            "entity_type": "dedup_review",
            "entity_id": str(match.candidate_id),
            "metadata": {
                "review_type": "dedup",
                "candidate_id": str(match.candidate_id),
                "existing_candidate_id": str(match.existing_candidate_id),
                "confidence": match.confidence,
                "strategies": match.match_strategies,
                "details": match.details,
            },
        }
        supabase.table("signals").insert(signal).execute()


def _pick_best_field(existing_val, incoming_val):
    """Pick the best value for a field during merge."""
    if existing_val is not None and existing_val != "":
        return existing_val
    return incoming_val


def _merge_skills(existing: list[dict], incoming: list[dict]) -> list[dict]:
    """Merge two skill lists, deduplicating by name."""
    skill_map: dict[str, dict] = {}

    for skill in existing + incoming:
        name = skill.get("name", "").lower().strip()
        if not name:
            continue
        if name not in skill_map:
            skill_map[name] = skill
        else:
            if skill.get("confidence", 0) > skill_map[name].get(
                "confidence", 0
            ):
                skill_map[name] = skill
            if skill.get("years") and not skill_map[name].get("years"):
                skill_map[name]["years"] = skill["years"]

    return list(skill_map.values())


def _merge_experience(
    existing: list[dict], incoming: list[dict]
) -> list[dict]:
    """Merge two experience lists, deduplicating by company+title."""
    exp_map: dict[str, dict] = {}

    for exp in existing + incoming:
        key = f"{exp.get('company', '').lower()}|{exp.get('title', '').lower()}"
        if key not in exp_map:
            exp_map[key] = exp
        else:
            existing_score = sum(
                1 for v in exp_map[key].values() if v is not None
            )
            incoming_score = sum(1 for v in exp.values() if v is not None)
            if incoming_score > existing_score:
                exp_map[key] = exp

    return list(exp_map.values())
