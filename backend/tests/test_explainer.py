import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from contracts.shared import ConfidenceLevel
from matching.explainer import (
    CONFIDENCE_LABELS,
    EXPLANATION_SYSTEM_PROMPT,
    EXPLANATION_USER_PROMPT_TEMPLATE,
    MatchExplainer,
)


@pytest.fixture
def mock_supabase():
    return MagicMock()


@pytest.fixture
def explainer(mock_supabase):
    with patch("matching.explainer.AsyncOpenAI"):
        exp = MatchExplainer(mock_supabase)
        return exp


def test_confidence_labels():
    assert CONFIDENCE_LABELS[ConfidenceLevel.strong] == "Strong Match"
    assert CONFIDENCE_LABELS[ConfidenceLevel.good] == "Good Match"
    assert CONFIDENCE_LABELS[ConfidenceLevel.possible] == "Worth Considering"


def test_confidence_values_at_or_above(explainer):
    assert explainer._get_confidence_values_at_or_above(
        ConfidenceLevel.strong
    ) == ["strong"]
    assert explainer._get_confidence_values_at_or_above(
        ConfidenceLevel.good
    ) == ["good", "strong"]
    assert explainer._get_confidence_values_at_or_above(
        ConfidenceLevel.possible
    ) == ["possible", "good", "strong"]


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
    assert "never" in EXPLANATION_SYSTEM_PROMPT.lower()


def test_prompt_template_has_all_placeholders():
    required_placeholders = [
        "role_title",
        "required_skills",
        "preferred_skills",
        "role_seniority",
        "role_location",
        "role_industry",
        "candidate_title",
        "candidate_seniority",
        "candidate_location",
        "candidate_experience_years",
        "candidate_skills",
        "candidate_industries",
        "candidate_availability",
        "confidence_label",
        "skills_matched",
        "skills_partial",
        "skills_missing",
        "semantic_description",
        "experience_description",
    ]
    for placeholder in required_placeholders:
        assert f"{{{placeholder}}}" in EXPLANATION_USER_PROMPT_TEMPLATE


@pytest.mark.asyncio
async def test_generate_single_explanation_calls_openai(explainer):
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
        "experience": [
            {"title": "Backend Developer", "duration_months": 72}
        ],
        "industries": ["fintech"],
        "availability": "immediate",
    }

    mock_table = MagicMock()
    explainer.supabase.table.return_value = mock_table
    mock_select = MagicMock()
    mock_table.select.return_value = mock_select
    mock_eq = MagicMock()
    mock_select.eq.return_value = mock_eq
    mock_single = MagicMock()
    mock_eq.single.return_value = mock_single

    mock_single.execute.side_effect = [
        MagicMock(data=match_data),
        MagicMock(data=role_data),
        MagicMock(data=candidate_data),
    ]

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "explanation": "Alice is a strong match for this Senior Backend role.",
            "strengths": [
                "6 years of Python experience",
                "Fintech industry background",
            ],
            "gaps": ["No Go experience"],
            "recommendation": "Arrange an introductory call to discuss the role in detail.",
        }
    )
    explainer.openai.chat.completions.create = AsyncMock(
        return_value=mock_response
    )

    result = await explainer.generate_single_explanation(uuid4())

    assert result is not None
    assert "Alice" in result["explanation"]
    assert len(result["strengths"]) >= 1
    assert len(result["gaps"]) >= 1
    assert result["recommendation"] != ""
