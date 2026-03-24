# Agent A — Task 10: Match Explanation Generator

## Mission
Build the LLM-powered explanation generator that produces plain-English match explanations for top candidates, including bullet-point strengths, gaps, and a one-line recommendation.

## Context
This is Day 3. Task 09 has produced scored matches with full scoring breakdowns but empty explanation fields. This task fills in the human-readable explanations for Strong and Good matches (>= 0.5 overall score). The language must be non-technical — written for recruitment partners and hiring managers, not engineers. Every explanation tracks which model version generated it for quality monitoring.

## Prerequisites
- Task 09 complete (matching engine stores matches with scores, skill overlaps, breakdowns)
- Task 03 complete (FastAPI skeleton with OpenAI client configured)
- Task 07 complete (AI extraction pipeline — OpenAI client pattern established)
- `backend/contracts/match.py` exists with `Match` model including `explanation`, `strengths`, `gaps`, `recommendation`, `model_version`

## Checklist
- [ ] Create `backend/matching/explainer.py` — LLM explanation generator
- [ ] Add `generate_explanations` method that processes a batch of matches
- [ ] Add `generate_single_explanation` for on-demand re-generation
- [ ] Implement confidence-to-label mapping (Strong Match, Good Match, Worth Considering)
- [ ] Store model version with every generated explanation
- [ ] Create `backend/tests/test_explainer.py` — unit tests with mocked OpenAI
- [ ] Run tests, verify pass
- [ ] Commit: "Agent A Task 10: Match explanation generator"

## Implementation Details

### Explainer (`backend/matching/explainer.py`)

```python
import json
from uuid import UUID
from openai import AsyncOpenAI
from backend.config import settings
from backend.contracts.shared import ConfidenceLevel, SkillMatch
from supabase import Client


CONFIDENCE_LABELS = {
    ConfidenceLevel.strong: "Strong Match",
    ConfidenceLevel.good: "Good Match",
    ConfidenceLevel.possible: "Worth Considering",
}

EXPLANATION_SYSTEM_PROMPT = """You are an expert recruitment consultant writing match explanations for a UK-based recruitment platform. Your audience is non-technical recruitment partners and hiring managers.

Rules:
- Write in plain English. No jargon, no raw scores, no technical metrics.
- Be specific about the candidate's relevant experience and how it aligns with the role.
- Mention specific skills, years of experience, and industry context where relevant.
- Be honest about gaps — if skills are missing, say so constructively.
- Keep the tone professional but warm. Think "trusted advisor", not "algorithm output".
- Use UK English spelling (e.g., "organisation", "specialised").
- Never fabricate experience or skills — only reference what is provided in the data.
- Strengths and gaps should be concise bullet points (one line each).
- The recommendation should be a single actionable sentence.

You will receive structured data about a candidate and role match. Return your response as JSON."""

EXPLANATION_USER_PROMPT_TEMPLATE = """Generate a match explanation for this candidate-role pairing.

## Role
- Title: {role_title}
- Required Skills: {required_skills}
- Preferred Skills: {preferred_skills}
- Seniority: {role_seniority}
- Location: {role_location}
- Industry: {role_industry}

## Candidate
- Current/Recent Title: {candidate_title}
- Seniority: {candidate_seniority}
- Location: {candidate_location}
- Total Experience: {candidate_experience_years} years
- Key Skills: {candidate_skills}
- Industries: {candidate_industries}
- Availability: {candidate_availability}

## Match Data
- Confidence Level: {confidence_label}
- Skills Matched: {skills_matched}
- Skills Partially Matched: {skills_partial}
- Skills Missing: {skills_missing}
- Semantic Similarity: {semantic_description}
- Experience Fit: {experience_description}

Return JSON with this exact structure:
{{
    "explanation": "2-3 sentence plain-English explanation of why this candidate matches (or doesn't match) this role.",
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "gaps": ["gap 1", "gap 2"],
    "recommendation": "One actionable sentence recommending next steps."
}}"""


class MatchExplainer:
    """Generates plain-English match explanations using an LLM."""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.model_version = f"{settings.openai_model}-explainer-v1"

    async def generate_explanations(
        self,
        role_id: UUID,
        min_confidence: ConfidenceLevel = ConfidenceLevel.good,
    ) -> int:
        """
        Generate explanations for all matches of a role at or above min_confidence.
        Only processes matches that don't already have an explanation.

        Returns the count of explanations generated.
        """
        # Load matches that need explanations
        confidence_values = self._get_confidence_values_at_or_above(min_confidence)

        matches_result = self.supabase.table("matches").select("*") \
            .eq("role_id", str(role_id)) \
            .in_("confidence", confidence_values) \
            .or_("explanation.is.null,explanation.eq.") \
            .execute()

        matches = matches_result.data or []
        if not matches:
            return 0

        # Load the role
        role_result = self.supabase.table("roles").select("*") \
            .eq("id", str(role_id)).single().execute()
        role = role_result.data

        # Load candidates in batch
        candidate_ids = [m["candidate_id"] for m in matches]
        candidates_result = self.supabase.table("candidates").select("*") \
            .in_("id", candidate_ids).execute()
        candidates_map = {c["id"]: c for c in (candidates_result.data or [])}

        count = 0
        for match in matches:
            candidate = candidates_map.get(match["candidate_id"])
            if not candidate:
                continue

            explanation = await self._generate_single(role, candidate, match)
            if explanation:
                self.supabase.table("matches").update({
                    "explanation": explanation["explanation"],
                    "strengths": explanation["strengths"],
                    "gaps": explanation["gaps"],
                    "recommendation": explanation["recommendation"],
                    "model_version": self.model_version,
                }).eq("id", match["id"]).execute()
                count += 1

        return count

    async def generate_single_explanation(
        self,
        match_id: UUID,
    ) -> dict | None:
        """
        Re-generate explanation for a single match.
        Useful for on-demand regeneration after corrections.
        """
        match_result = self.supabase.table("matches").select("*") \
            .eq("id", str(match_id)).single().execute()
        match = match_result.data
        if not match:
            return None

        role_result = self.supabase.table("roles").select("*") \
            .eq("id", match["role_id"]).single().execute()
        role = role_result.data

        candidate_result = self.supabase.table("candidates").select("*") \
            .eq("id", match["candidate_id"]).single().execute()
        candidate = candidate_result.data

        if not role or not candidate:
            return None

        explanation = await self._generate_single(role, candidate, match)
        if explanation:
            self.supabase.table("matches").update({
                "explanation": explanation["explanation"],
                "strengths": explanation["strengths"],
                "gaps": explanation["gaps"],
                "recommendation": explanation["recommendation"],
                "model_version": self.model_version,
            }).eq("id", match["id"]).execute()

        return explanation

    async def _generate_single(
        self,
        role: dict,
        candidate: dict,
        match: dict,
    ) -> dict | None:
        """Generate explanation for a single candidate-role match."""
        # Parse skill overlaps
        skill_overlap = match.get("skill_overlap") or []
        skills_matched = [s["skill_name"] for s in skill_overlap if s.get("status") == "matched"]
        skills_partial = [s["skill_name"] for s in skill_overlap if s.get("status") == "partial"]
        skills_missing = [s["skill_name"] for s in skill_overlap if s.get("status") == "missing"]

        # Build semantic description from score
        semantic_score = match.get("semantic_score", 0)
        if semantic_score > 0.8:
            semantic_description = "Very high profile similarity — candidate's overall experience closely mirrors the role requirements"
        elif semantic_score > 0.6:
            semantic_description = "Good profile similarity — significant overlap in experience and domain"
        elif semantic_score > 0.4:
            semantic_description = "Moderate profile similarity — some relevant overlap"
        else:
            semantic_description = "Lower profile similarity — candidate's background differs from typical candidates for this role"

        # Build experience description
        experience_score = match.get("scoring_breakdown", {}).get("components", {}).get("experience_fit_raw", 0.5)
        if experience_score >= 0.9:
            experience_description = "Excellent seniority and experience match"
        elif experience_score >= 0.6:
            experience_description = "Good experience level, close to requirements"
        else:
            experience_description = "Experience level differs from role requirements"

        # Get most recent job title
        experience = candidate.get("experience") or []
        candidate_title = experience[0].get("title", "Not specified") if experience else "Not specified"

        # Candidate skills summary
        candidate_skills_list = candidate.get("skills") or []
        candidate_skills_str = ", ".join(
            f"{s['name']} ({s.get('years', '?')}y)"
            for s in candidate_skills_list[:10]
        ) or "None extracted"

        # Build confidence label
        confidence = ConfidenceLevel(match.get("confidence", "possible"))
        confidence_label = CONFIDENCE_LABELS.get(confidence, "Worth Considering")

        # Total experience years
        total_months = sum(
            (e.get("duration_months") or 0)
            for e in experience if isinstance(e, dict)
        )

        prompt = EXPLANATION_USER_PROMPT_TEMPLATE.format(
            role_title=role.get("title", ""),
            required_skills=", ".join(
                s.get("name", "") for s in (role.get("required_skills") or [])
            ) or "None specified",
            preferred_skills=", ".join(
                s.get("name", "") for s in (role.get("preferred_skills") or [])
            ) or "None specified",
            role_seniority=role.get("seniority", "Not specified"),
            role_location=role.get("location", "Not specified"),
            role_industry=role.get("industry", "Not specified"),
            candidate_title=candidate_title,
            candidate_seniority=candidate.get("seniority", "Not specified"),
            candidate_location=candidate.get("location", "Not specified"),
            candidate_experience_years=round(total_months / 12, 1),
            candidate_skills=candidate_skills_str,
            candidate_industries=", ".join(candidate.get("industries") or []) or "Not specified",
            candidate_availability=candidate.get("availability", "Not specified"),
            confidence_label=confidence_label,
            skills_matched=", ".join(skills_matched) or "None",
            skills_partial=", ".join(skills_partial) or "None",
            skills_missing=", ".join(skills_missing) or "None",
            semantic_description=semantic_description,
            experience_description=experience_description,
        )

        try:
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": EXPLANATION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=500,
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            # Validate structure
            return {
                "explanation": result.get("explanation", ""),
                "strengths": result.get("strengths", [])[:5],  # cap at 5
                "gaps": result.get("gaps", [])[:5],
                "recommendation": result.get("recommendation", ""),
            }

        except Exception as e:
            # Fallback: generate a basic explanation from structured data
            return self._generate_fallback(
                confidence_label, skills_matched, skills_partial,
                skills_missing, candidate, role
            )

    def _generate_fallback(
        self,
        confidence_label: str,
        skills_matched: list[str],
        skills_partial: list[str],
        skills_missing: list[str],
        candidate: dict,
        role: dict,
    ) -> dict:
        """Generate a basic explanation without LLM as fallback."""
        name = candidate.get("first_name", "Candidate")
        role_title = role.get("title", "this role")

        explanation_parts = []
        if skills_matched:
            explanation_parts.append(
                f"{name} brings relevant experience in {', '.join(skills_matched[:3])}."
            )
        if skills_missing:
            explanation_parts.append(
                f"However, experience in {', '.join(skills_missing[:2])} would strengthen the match."
            )

        explanation = " ".join(explanation_parts) or f"{name} has been identified as a {confidence_label.lower()} for {role_title}."

        strengths = [f"Experience with {s}" for s in skills_matched[:3]]
        gaps = [f"No demonstrated experience in {s}" for s in skills_missing[:3]]
        recommendation = f"Consider {name} for an introductory conversation to assess cultural fit and specific experience depth."

        return {
            "explanation": explanation,
            "strengths": strengths,
            "gaps": gaps,
            "recommendation": recommendation,
        }

    def _get_confidence_values_at_or_above(
        self, min_confidence: ConfidenceLevel
    ) -> list[str]:
        """Return confidence level values at or above the minimum."""
        order = [ConfidenceLevel.possible, ConfidenceLevel.good, ConfidenceLevel.strong]
        idx = order.index(min_confidence)
        return [c.value for c in order[idx:]]
```

### Tests (`backend/tests/test_explainer.py`)

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from backend.matching.explainer import (
    MatchExplainer, CONFIDENCE_LABELS,
    EXPLANATION_SYSTEM_PROMPT, EXPLANATION_USER_PROMPT_TEMPLATE
)
from backend.contracts.shared import ConfidenceLevel


@pytest.fixture
def mock_supabase():
    return MagicMock()


@pytest.fixture
def explainer(mock_supabase):
    with patch("backend.matching.explainer.AsyncOpenAI"):
        exp = MatchExplainer(mock_supabase)
        return exp


def test_confidence_labels():
    assert CONFIDENCE_LABELS[ConfidenceLevel.strong] == "Strong Match"
    assert CONFIDENCE_LABELS[ConfidenceLevel.good] == "Good Match"
    assert CONFIDENCE_LABELS[ConfidenceLevel.possible] == "Worth Considering"


def test_confidence_values_at_or_above(explainer):
    assert explainer._get_confidence_values_at_or_above(ConfidenceLevel.strong) == ["strong"]
    assert explainer._get_confidence_values_at_or_above(ConfidenceLevel.good) == ["good", "strong"]
    assert explainer._get_confidence_values_at_or_above(ConfidenceLevel.possible) == ["possible", "good", "strong"]


def test_fallback_explanation(explainer):
    result = explainer._generate_fallback(
        confidence_label="Strong Match",
        skills_matched=["Python", "FastAPI", "PostgreSQL"],
        skills_partial=["React"],
        skills_missing=["Go"],
        candidate={"first_name": "Sarah"},
        role={"title": "Senior Backend Engineer"},
    )

    assert "Sarah" in result["explanation"]
    assert "Python" in result["explanation"]
    assert len(result["strengths"]) > 0
    assert len(result["gaps"]) > 0
    assert "Sarah" in result["recommendation"]
    assert isinstance(result["strengths"], list)
    assert isinstance(result["gaps"], list)


def test_fallback_no_skills(explainer):
    result = explainer._generate_fallback(
        confidence_label="Worth Considering",
        skills_matched=[],
        skills_partial=[],
        skills_missing=["Python", "Go"],
        candidate={"first_name": "James"},
        role={"title": "Backend Engineer"},
    )

    assert "James" in result["explanation"]
    assert len(result["gaps"]) > 0


def test_system_prompt_contains_uk_english_rule():
    assert "UK English" in EXPLANATION_SYSTEM_PROMPT


def test_system_prompt_forbids_fabrication():
    assert "fabricate" in EXPLANATION_SYSTEM_PROMPT.lower() or "never" in EXPLANATION_SYSTEM_PROMPT.lower()


def test_prompt_template_has_all_placeholders():
    required_placeholders = [
        "role_title", "required_skills", "preferred_skills",
        "role_seniority", "role_location", "role_industry",
        "candidate_title", "candidate_seniority", "candidate_location",
        "candidate_experience_years", "candidate_skills",
        "candidate_industries", "candidate_availability",
        "confidence_label", "skills_matched", "skills_partial",
        "skills_missing", "semantic_description", "experience_description",
    ]
    for placeholder in required_placeholders:
        assert f"{{{placeholder}}}" in EXPLANATION_USER_PROMPT_TEMPLATE


@pytest.mark.asyncio
async def test_generate_single_explanation_calls_openai(explainer):
    # Mock the supabase responses
    match_data = {
        "id": str(uuid4()),
        "candidate_id": str(uuid4()),
        "role_id": str(uuid4()),
        "confidence": "strong",
        "semantic_score": 0.85,
        "skill_overlap": [
            {"skill_name": "Python", "status": "matched"},
            {"skill_name": "Go", "status": "missing"},
        ],
        "scoring_breakdown": {"components": {"experience_fit_raw": 0.9}},
    }

    role_data = {
        "title": "Senior Backend Engineer",
        "required_skills": [{"name": "Python"}],
        "preferred_skills": [{"name": "Go"}],
        "seniority": "senior",
        "location": "London",
        "industry": "fintech",
    }

    candidate_data = {
        "first_name": "Alice",
        "seniority": "senior",
        "location": "London",
        "skills": [{"name": "Python", "years": 6}],
        "experience": [{"title": "Backend Developer", "duration_months": 72}],
        "industries": ["fintech"],
        "availability": "immediate",
    }

    # Set up mock chain
    mock_table = MagicMock()
    explainer.supabase.table.return_value = mock_table
    mock_select = MagicMock()
    mock_table.select.return_value = mock_select
    mock_eq = MagicMock()
    mock_select.eq.return_value = mock_eq
    mock_single = MagicMock()
    mock_eq.single.return_value = mock_single

    # Return different data depending on call order
    mock_single.execute.side_effect = [
        MagicMock(data=match_data),
        MagicMock(data=role_data),
        MagicMock(data=candidate_data),
    ]

    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "explanation": "Alice is a strong match for this Senior Backend role.",
        "strengths": ["6 years of Python experience", "Fintech industry background"],
        "gaps": ["No Go experience"],
        "recommendation": "Arrange an introductory call to discuss the role in detail.",
    })
    explainer.openai.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await explainer.generate_single_explanation(uuid4())

    assert result is not None
    assert "Alice" in result["explanation"]
    assert len(result["strengths"]) >= 1
    assert len(result["gaps"]) >= 1
    assert result["recommendation"] != ""


import json  # needed for test above
```

## Outputs
- `backend/matching/explainer.py`
- `backend/tests/test_explainer.py`

## Acceptance Criteria
1. `python -m pytest tests/test_explainer.py -v` — all tests pass
2. Explanations are 2-3 sentences of plain English, no raw scores or technical jargon
3. Strengths and gaps are concise bullet points (capped at 5 each)
4. Recommendation is a single actionable sentence
5. Confidence maps to human labels: "Strong Match", "Good Match", "Worth Considering"
6. Model version is tracked with every explanation (stored in `model_version` field)
7. Fallback explanation works when OpenAI is unavailable (no crash, degraded but functional)
8. Batch generation processes all qualifying matches for a role
9. Single re-generation works for on-demand updates
10. Prompt uses UK English and forbids skill/experience fabrication

## Handoff Notes
- **To Task 11:** Explanations are now populated on matches. The match API endpoint should return the full explanation, strengths, gaps, and recommendation fields.
- **To Agent B:** The `explanation` field is 2-3 sentences for the match card. `strengths` and `gaps` are arrays of bullet-point strings. `recommendation` is one line. `confidence` is an enum that maps to the labels "Strong Match" / "Good Match" / "Worth Considering" — display these as badges. The `model_version` field is for admin traceability views.
- **Decision:** Only Strong and Good matches (>= 0.5) get LLM explanations by default. Possible matches get fallback explanations to save API costs. Batch processing is sequential (not parallel) to respect rate limits. Temperature 0.3 for consistent, factual output.
