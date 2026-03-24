# Agent A — Task 06: Deduplication Pipeline

## Mission
Build the identity resolution and deduplication pipeline with three matching strategies (exact, fuzzy, semantic), automatic merging for high-confidence matches, review queuing for uncertain matches, and merge logic that preserves the most complete data per field while maintaining all source attributions.

## Context
Day 2 task, depends on Task 05 (ingestion pipeline). Candidates arrive from multiple adapters with overlapping records (same person in Bullhorn, HubSpot, and LinkedIn). The dedup pipeline runs after ingestion to identify and merge duplicate records. Three confidence tiers: auto-merge (>0.9), human review (0.6-0.9), and no match (<0.6). The merged candidate retains the best data from each source.

## Prerequisites
- Task 05 complete (ingestion stores candidates in Supabase)
- Task 02 complete (candidates table with `dedup_group`, `dedup_confidence` columns)
- Task 01 complete (contracts)
- `Levenshtein` package installed (in requirements.txt)

## Checklist
- [ ] Create `backend/pipelines/deduplicate.py`
- [ ] Implement exact match strategy (email, phone)
- [ ] Implement fuzzy match strategy (Levenshtein on name + employer)
- [ ] Implement semantic match strategy (embedding similarity > 0.95)
- [ ] Implement confidence scoring that combines strategy results
- [ ] Implement auto-merge for confidence > 0.9
- [ ] Implement review queue for confidence 0.6-0.9
- [ ] Implement merge logic — best data per field, combined sources
- [ ] Handle skill list deduplication during merge
- [ ] Log dedup decisions as signal events
- [ ] Add dedup review table/queue support
- [ ] Write comprehensive tests
- [ ] Commit

## Implementation Details

### Deduplication Pipeline (`backend/pipelines/deduplicate.py`)

```python
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel
from Levenshtein import ratio as levenshtein_ratio
from api.deps import get_supabase_admin
from contracts.shared import SignalType, UserRole
import logging

logger = logging.getLogger("recruittech.pipelines.deduplicate")


class DedupMatch(BaseModel):
    """A potential duplicate match between two candidate records."""
    candidate_id: UUID
    existing_candidate_id: UUID
    confidence: float
    match_strategies: list[str]  # which strategies triggered
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

    # Confidence thresholds
    AUTO_MERGE_THRESHOLD = 0.9
    REVIEW_THRESHOLD = 0.6

    # Strategy weights for combined confidence
    EXACT_MATCH_CONFIDENCE = 0.95
    FUZZY_NAME_THRESHOLD = 0.85  # minimum Levenshtein ratio for name
    FUZZY_EMPLOYER_THRESHOLD = 0.80
    SEMANTIC_THRESHOLD = 0.95  # cosine similarity threshold

    async def run(
        self,
        candidate_ids: list[UUID] | None = None,
    ) -> DedupResult:
        """Run deduplication on specified candidates or all un-deduped candidates.

        Args:
            candidate_ids: Specific candidates to check. If None, checks all
                          candidates without a dedup_group.
        """
        supabase = get_supabase_admin()

        # Fetch candidates to check
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

        # Fetch all existing candidates for comparison
        all_result = supabase.table("candidates").select(
            "id, first_name, last_name, email, phone, experience, embedding, sources"
        ).execute()
        existing_candidates = all_result.data or []

        decisions: list[DedupDecision] = []
        auto_merged = 0
        queued = 0
        no_match_count = 0

        for candidate in new_candidates:
            candidate_id = UUID(candidate["id"])

            # Find best match among existing candidates (excluding self)
            best_match = await self._find_best_match(
                candidate, existing_candidates
            )

            if best_match is None:
                no_match_count += 1
                # Assign own dedup group (unique)
                group_id = uuid4()
                await self._set_dedup_group(
                    supabase, candidate_id, group_id, confidence=1.0
                )
                continue

            if best_match.confidence >= self.AUTO_MERGE_THRESHOLD:
                # Auto-merge
                merged_id = await self._merge_candidates(
                    supabase, candidate_id, best_match.existing_candidate_id
                )
                decisions.append(DedupDecision(
                    match=best_match,
                    action="auto_merged",
                    merged_candidate_id=merged_id,
                ))
                auto_merged += 1
                logger.info(
                    f"Auto-merged {candidate_id} into "
                    f"{best_match.existing_candidate_id} "
                    f"(confidence: {best_match.confidence:.2f})"
                )

            elif best_match.confidence >= self.REVIEW_THRESHOLD:
                # Queue for human review
                await self._queue_for_review(supabase, best_match)
                decisions.append(DedupDecision(
                    match=best_match,
                    action="queued_for_review",
                ))
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

            if confidence > best_confidence and confidence >= self.REVIEW_THRESHOLD:
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
        """Compute combined match confidence from all strategies.

        Returns: (confidence, strategies_used, details)
        """
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

        # Combined confidence: take max confidence, boost if multiple strategies agree
        max_conf = max(confidences)
        if len(strategies) >= 2:
            # Multiple strategies agree — boost confidence
            max_conf = min(1.0, max_conf + 0.05 * (len(strategies) - 1))

        return round(max_conf, 3), strategies, details

    def _exact_email_match(self, candidate: dict, existing: dict) -> float:
        """Exact email match → high confidence."""
        c_email = (candidate.get("email") or "").lower().strip()
        e_email = (existing.get("email") or "").lower().strip()
        if c_email and e_email and c_email == e_email:
            return self.EXACT_MATCH_CONFIDENCE
        return 0.0

    def _exact_phone_match(self, candidate: dict, existing: dict) -> float:
        """Exact phone match (normalized) → high confidence."""
        def normalize_phone(p: str | None) -> str:
            if not p:
                return ""
            import re
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

        # Name similarity
        c_name = f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}".lower().strip()
        e_name = f"{existing.get('first_name', '')} {existing.get('last_name', '')}".lower().strip()

        if not c_name or not e_name:
            return 0.0, details

        name_ratio = levenshtein_ratio(c_name, e_name)
        details["name_similarity"] = round(name_ratio, 3)

        if name_ratio < self.FUZZY_NAME_THRESHOLD:
            return 0.0, details

        # Employer similarity (from most recent experience)
        c_employer = self._get_current_employer(candidate)
        e_employer = self._get_current_employer(existing)

        if c_employer and e_employer:
            employer_ratio = levenshtein_ratio(
                c_employer.lower(), e_employer.lower()
            )
            details["employer_similarity"] = round(employer_ratio, 3)

            if employer_ratio >= self.FUZZY_EMPLOYER_THRESHOLD:
                # Name + employer match — good confidence
                combined = (name_ratio * 0.6) + (employer_ratio * 0.4)
                return round(min(combined, 0.88), 3), details  # cap below auto-merge

        # Name match only (no employer) — lower confidence
        if name_ratio >= 0.95:
            return round(name_ratio * 0.7, 3), details

        return 0.0, details

    def _semantic_match(self, candidate: dict, existing: dict) -> float:
        """Semantic match using embedding cosine similarity."""
        c_embedding = candidate.get("embedding")
        e_embedding = existing.get("embedding")

        if not c_embedding or not e_embedding:
            return 0.0

        # Cosine similarity
        similarity = self._cosine_similarity(c_embedding, e_embedding)
        if similarity >= self.SEMANTIC_THRESHOLD:
            return round(similarity, 3)

        return 0.0

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        import math
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
        """Merge incoming candidate into existing candidate.

        Merge logic:
        - Keep the most complete (non-null) data per field
        - Combine skills lists (deduplicated by name)
        - Combine experience lists
        - Combine sources arrays
        - Use highest confidence extraction data
        - Set shared dedup_group
        """
        # Fetch both full records
        incoming = supabase.table("candidates").select("*").eq(
            "id", str(incoming_id)
        ).single().execute().data
        existing = supabase.table("candidates").select("*").eq(
            "id", str(existing_id)
        ).single().execute().data

        # Merge fields — prefer non-null, then prefer existing (more established)
        merged = {}
        MERGE_FIELDS = [
            "email", "phone", "location", "linkedin_url",
            "cv_text", "profile_text", "seniority",
            "salary_expectation", "availability",
        ]
        for field in MERGE_FIELDS:
            merged[field] = _pick_best_field(
                existing.get(field), incoming.get(field)
            )

        # Merge skills — deduplicate by name, keep higher confidence
        merged_skills = _merge_skills(
            existing.get("skills", []),
            incoming.get("skills", []),
        )

        # Merge experience — combine, deduplicate by company+title
        merged_experience = _merge_experience(
            existing.get("experience", []),
            incoming.get("experience", []),
        )

        # Combine sources
        merged_sources = existing.get("sources", []) + incoming.get("sources", [])

        # Combine industries (deduplicate)
        merged_industries = list(set(
            existing.get("industries", []) + incoming.get("industries", [])
        ))

        # Best extraction confidence
        existing_conf = existing.get("extraction_confidence") or 0.0
        incoming_conf = incoming.get("extraction_confidence") or 0.0
        best_conf = max(existing_conf, incoming_conf)

        # Merge embedding — prefer one that exists, or existing
        merged_embedding = existing.get("embedding") or incoming.get("embedding")

        # Dedup group
        group_id = existing.get("dedup_group") or str(uuid4())

        # Update existing record with merged data
        update_data = {
            **merged,
            "skills": merged_skills,
            "experience": merged_experience,
            "sources": merged_sources,
            "industries": merged_industries,
            "extraction_confidence": best_conf if best_conf > 0 else None,
            "embedding": merged_embedding,
            "dedup_group": group_id,
            "dedup_confidence": 1.0,  # merged record is definitive
        }
        supabase.table("candidates").update(update_data).eq(
            "id", str(existing_id)
        ).execute()

        # Mark incoming record as merged (set dedup_group, could also soft-delete)
        supabase.table("candidates").update({
            "dedup_group": group_id,
            "dedup_confidence": 0.0,  # signals this is the non-primary record
        }).eq("id", str(incoming_id)).execute()

        return existing_id

    async def _set_dedup_group(
        self,
        supabase,
        candidate_id: UUID,
        group_id: UUID,
        confidence: float,
    ) -> None:
        """Set dedup_group on a candidate."""
        supabase.table("candidates").update({
            "dedup_group": str(group_id),
            "dedup_confidence": confidence,
        }).eq("id", str(candidate_id)).execute()

    async def _queue_for_review(
        self,
        supabase,
        match: DedupMatch,
    ) -> None:
        """Add a potential duplicate to the review queue.

        Stores in signals table as a special event for admin review.
        """
        signal = {
            "id": str(uuid4()),
            "event_type": "candidate_ingested",  # reuse type, metadata distinguishes
            "actor_id": str(match.candidate_id),  # system as actor
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
    """Pick the best value for a field during merge.

    Priority: non-null > null, existing > incoming (when both non-null).
    """
    if existing_val is not None and existing_val != "":
        return existing_val
    return incoming_val


def _merge_skills(existing: list[dict], incoming: list[dict]) -> list[dict]:
    """Merge two skill lists, deduplicating by name.

    When same skill appears in both, keep the one with higher confidence.
    """
    skill_map: dict[str, dict] = {}

    for skill in existing + incoming:
        name = skill.get("name", "").lower().strip()
        if not name:
            continue
        if name not in skill_map:
            skill_map[name] = skill
        else:
            # Keep higher confidence version
            if skill.get("confidence", 0) > skill_map[name].get("confidence", 0):
                skill_map[name] = skill
            # If incoming has years info and existing doesn't, take incoming years
            if skill.get("years") and not skill_map[name].get("years"):
                skill_map[name]["years"] = skill["years"]

    return list(skill_map.values())


def _merge_experience(existing: list[dict], incoming: list[dict]) -> list[dict]:
    """Merge two experience lists, deduplicating by company+title.

    When same position appears in both, keep the one with more data
    (e.g., the one with duration_months set).
    """
    exp_map: dict[str, dict] = {}

    for exp in existing + incoming:
        key = f"{exp.get('company', '').lower()}|{exp.get('title', '').lower()}"
        if key not in exp_map:
            exp_map[key] = exp
        else:
            # Keep the version with more data
            existing_score = sum(1 for v in exp_map[key].values() if v is not None)
            incoming_score = sum(1 for v in exp.values() if v is not None)
            if incoming_score > existing_score:
                exp_map[key] = exp

    return list(exp_map.values())
```

### Tests (`backend/tests/test_deduplicate.py`)

```python
import pytest
from uuid import uuid4
from pipelines.deduplicate import (
    DeduplicationPipeline,
    _pick_best_field,
    _merge_skills,
    _merge_experience,
)


class TestPickBestField:
    def test_existing_preferred(self):
        assert _pick_best_field("existing", "incoming") == "existing"

    def test_incoming_when_existing_null(self):
        assert _pick_best_field(None, "incoming") == "incoming"

    def test_existing_when_incoming_null(self):
        assert _pick_best_field("existing", None) == "existing"

    def test_both_null(self):
        assert _pick_best_field(None, None) is None

    def test_empty_string_treated_as_null(self):
        assert _pick_best_field("", "incoming") == "incoming"


class TestMergeSkills:
    def test_no_overlap(self):
        existing = [{"name": "Python", "confidence": 0.9}]
        incoming = [{"name": "Java", "confidence": 0.8}]
        result = _merge_skills(existing, incoming)
        assert len(result) == 2

    def test_overlapping_keeps_higher_confidence(self):
        existing = [{"name": "Python", "confidence": 0.7}]
        incoming = [{"name": "Python", "confidence": 0.9}]
        result = _merge_skills(existing, incoming)
        assert len(result) == 1
        assert result[0]["confidence"] == 0.9

    def test_case_insensitive(self):
        existing = [{"name": "python", "confidence": 0.9}]
        incoming = [{"name": "Python", "confidence": 0.8}]
        result = _merge_skills(existing, incoming)
        assert len(result) == 1

    def test_years_preserved(self):
        existing = [{"name": "Python", "confidence": 0.9, "years": None}]
        incoming = [{"name": "Python", "confidence": 0.7, "years": 5.0}]
        result = _merge_skills(existing, incoming)
        assert result[0].get("years") == 5.0


class TestMergeExperience:
    def test_no_overlap(self):
        existing = [{"company": "Revolut", "title": "Senior Engineer"}]
        incoming = [{"company": "Monzo", "title": "Backend Engineer"}]
        result = _merge_experience(existing, incoming)
        assert len(result) == 2

    def test_dedup_same_position(self):
        existing = [{"company": "Revolut", "title": "Senior Engineer", "duration_months": None}]
        incoming = [{"company": "Revolut", "title": "Senior Engineer", "duration_months": 24}]
        result = _merge_experience(existing, incoming)
        assert len(result) == 1
        assert result[0]["duration_months"] == 24


class TestMatchConfidence:
    def setup_method(self):
        self.pipeline = DeduplicationPipeline()

    def test_exact_email_match(self):
        candidate = {"email": "james@example.com", "first_name": "James", "last_name": "Hartley"}
        existing = {"email": "james@example.com", "first_name": "J", "last_name": "H"}
        confidence, strategies, _ = self.pipeline._compute_match_confidence(candidate, existing)
        assert confidence >= 0.9
        assert "exact_email" in strategies

    def test_exact_phone_match(self):
        candidate = {"phone": "+44 7700 100001", "first_name": "James", "last_name": "Hartley"}
        existing = {"phone": "+447700100001", "first_name": "J", "last_name": "H"}
        confidence, strategies, _ = self.pipeline._compute_match_confidence(candidate, existing)
        assert confidence >= 0.9
        assert "exact_phone" in strategies

    def test_fuzzy_name_employer_match(self):
        candidate = {
            "first_name": "James", "last_name": "Hartley",
            "experience": [{"company": "Revolut"}],
        }
        existing = {
            "first_name": "James", "last_name": "Hartley",
            "experience": [{"company": "Revolut"}],
        }
        confidence, strategies, _ = self.pipeline._compute_match_confidence(candidate, existing)
        assert confidence >= 0.6
        assert "fuzzy_name_employer" in strategies

    def test_no_match(self):
        candidate = {"first_name": "Alice", "last_name": "Smith", "email": "alice@example.com"}
        existing = {"first_name": "Bob", "last_name": "Jones", "email": "bob@example.com"}
        confidence, strategies, _ = self.pipeline._compute_match_confidence(candidate, existing)
        assert confidence < 0.6

    def test_multiple_strategies_boost(self):
        candidate = {
            "email": "james@example.com",
            "first_name": "James", "last_name": "Hartley",
            "experience": [{"company": "Revolut"}],
        }
        existing = {
            "email": "james@example.com",
            "first_name": "James", "last_name": "Hartley",
            "experience": [{"company": "Revolut"}],
        }
        confidence, strategies, _ = self.pipeline._compute_match_confidence(candidate, existing)
        # Multiple strategies should boost above single strategy
        assert len(strategies) >= 2
        assert confidence > 0.9
```

## Outputs
- `backend/pipelines/deduplicate.py`
- `backend/tests/test_deduplicate.py`

## Acceptance Criteria
1. Exact email match produces confidence >= 0.95
2. Exact phone match (with normalization) produces confidence >= 0.95
3. Fuzzy name + employer match produces confidence 0.6-0.9
4. Multiple strategies agreeing boosts confidence
5. Auto-merge (>0.9) merges candidates: combined sources, deduplicated skills, best-per-field data
6. Review queue (0.6-0.9) creates a signal event for admin review
7. No match (<0.6) assigns a unique dedup_group
8. Skill merge keeps higher confidence, preserves years data
9. Experience merge deduplicates by company+title, keeps most complete entry
10. `python -m pytest tests/test_deduplicate.py -v` — all tests pass

## Handoff Notes
- **To Task 07:** Dedup runs after ingestion, before AI extraction. If candidates are merged, the AI extraction pipeline should run on the merged record (existing_id), not the incoming duplicate.
- **To Task 08:** Candidate creation endpoints should trigger dedup check. Import `DeduplicationPipeline` and call `run(candidate_ids=[new_id])` after insert.
- **To Task 15 (Admin):** The admin dedup review queue is stored as signal events with `entity_type="dedup_review"`. Admin endpoints should query these and provide merge/keep-separate actions.
- **Decision:** Semantic matching requires embeddings to exist on both candidates. If embeddings are not yet generated (pre-extraction), this strategy is silently skipped. This is correct — semantic dedup is a second-pass strategy.
- **Decision:** The non-primary duplicate record is kept in the database with `dedup_confidence=0.0` as a soft indicator. This allows admin to review and potentially split incorrectly merged records.
