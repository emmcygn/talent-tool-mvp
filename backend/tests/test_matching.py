import pytest

from contracts.shared import (
    ConfidenceLevel,
    ExtractedSkill,
    RequiredSkill,
    SeniorityLevel,
)
from matching.scorer import CompositeScorer


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
        ExtractedSkill(name="Python", years=2),
    ]
    required = [
        RequiredSkill(name="Python", min_years=5),
        RequiredSkill(name="Go"),
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

    # Possible: low scores
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
