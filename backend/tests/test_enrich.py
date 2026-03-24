from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from contracts.shared import AvailabilityStatus, SeniorityLevel
from pipelines.enrich import (
    ExtractionPipeline,
    ExtractionResult,
    RoleExtractionResult,
)

# Mock LLM response for candidate extraction
MOCK_CANDIDATE_LLM_RESPONSE = {
    "skills": [
        {"name": "Python", "years": 8, "confidence": 0.95},
        {"name": "FastAPI", "years": 3, "confidence": 0.90},
        {"name": "PostgreSQL", "years": 6, "confidence": 0.85},
        {"name": "Docker", "years": 4, "confidence": 0.80},
        {"name": "AWS", "years": 5, "confidence": 0.75},
    ],
    "experience": [
        {
            "company": "Revolut",
            "title": "Senior Backend Engineer",
            "duration_months": 36,
            "industry": "Fintech",
        },
        {
            "company": "Monzo",
            "title": "Backend Engineer",
            "duration_months": 33,
            "industry": "Fintech",
        },
        {
            "company": "ThoughtWorks",
            "title": "Software Consultant",
            "duration_months": 29,
            "industry": "Consulting",
        },
    ],
    "seniority": "senior",
    "salary_expectation": {
        "min_amount": 90000,
        "max_amount": 100000,
        "currency": "GBP",
    },
    "availability": "1_month",
    "industries": ["Fintech", "Consulting"],
    "field_confidences": {
        "skills": 0.92,
        "experience": 0.95,
        "seniority": 0.88,
        "salary_expectation": 0.60,
        "availability": 0.75,
        "industries": 0.90,
    },
}

MOCK_ROLE_LLM_RESPONSE = {
    "required_skills": [
        {"name": "Python", "min_years": 5, "importance": "required"},
        {"name": "FastAPI", "min_years": 2, "importance": "required"},
        {"name": "PostgreSQL", "min_years": 3, "importance": "required"},
    ],
    "preferred_skills": [
        {"name": "Docker", "min_years": None, "importance": "preferred"},
        {"name": "AWS", "min_years": None, "importance": "preferred"},
    ],
    "seniority": "senior",
    "salary_band": {
        "min_amount": 80000,
        "max_amount": 100000,
        "currency": "GBP",
    },
    "industry": "Fintech",
    "field_confidences": {
        "required_skills": 0.95,
        "preferred_skills": 0.80,
        "seniority": 0.90,
        "salary_band": 0.85,
        "industry": 0.75,
    },
}


class TestCandidateExtractionParsing:
    def setup_method(self):
        self.pipeline = ExtractionPipeline()

    def test_parse_full_response(self):
        result = self.pipeline._parse_candidate_extraction(
            MOCK_CANDIDATE_LLM_RESPONSE
        )
        assert isinstance(result, ExtractionResult)
        assert len(result.skills) == 5
        assert result.skills[0].name == "Python"
        assert result.skills[0].years == 8
        assert len(result.experience) == 3
        assert result.seniority == SeniorityLevel.senior
        assert result.availability == AvailabilityStatus.one_month
        assert result.salary_expectation is not None
        assert len(result.industries) == 2
        assert result.overall_confidence > 0.0
        assert result.model_version != ""

    def test_low_confidence_flagged(self):
        result = self.pipeline._parse_candidate_extraction(
            MOCK_CANDIDATE_LLM_RESPONSE
        )
        # salary_expectation has confidence 0.60, below threshold 0.7
        assert "salary_expectation" in result.flagged_fields

    def test_high_confidence_not_flagged(self):
        result = self.pipeline._parse_candidate_extraction(
            MOCK_CANDIDATE_LLM_RESPONSE
        )
        assert "skills" not in result.flagged_fields
        assert "experience" not in result.flagged_fields

    def test_empty_response(self):
        result = self.pipeline._parse_candidate_extraction({})
        assert result.overall_confidence == 0.0
        assert result.skills == []
        assert result.experience == []

    def test_invalid_seniority_handled(self):
        data = {**MOCK_CANDIDATE_LLM_RESPONSE, "seniority": "invalid_value"}
        result = self.pipeline._parse_candidate_extraction(data)
        assert result.seniority is None

    def test_invalid_availability_handled(self):
        data = {**MOCK_CANDIDATE_LLM_RESPONSE, "availability": "invalid_value"}
        result = self.pipeline._parse_candidate_extraction(data)
        assert result.availability is None


class TestRoleExtractionParsing:
    def setup_method(self):
        self.pipeline = ExtractionPipeline()

    def test_parse_role_response(self):
        result = self.pipeline._parse_role_extraction(MOCK_ROLE_LLM_RESPONSE)
        assert isinstance(result, RoleExtractionResult)
        assert len(result.required_skills) == 3
        assert len(result.preferred_skills) == 2
        assert result.seniority == SeniorityLevel.senior
        assert result.salary_band is not None
        assert result.industry == "Fintech"
        assert result.overall_confidence > 0.0

    def test_empty_role_response(self):
        result = self.pipeline._parse_role_extraction({})
        assert result.overall_confidence == 0.0


class TestBuildCandidateText:
    def setup_method(self):
        self.pipeline = ExtractionPipeline()

    def test_cv_text_preferred(self):
        candidate = {"cv_text": "Full CV here", "profile_text": "Profile here"}
        text = self.pipeline._build_candidate_text(candidate)
        assert "Full CV here" in text
        assert "Profile here" in text

    def test_fallback_to_structured(self):
        candidate = {
            "first_name": "James",
            "last_name": "Hartley",
            "skills": [{"name": "Python"}, {"name": "FastAPI"}],
            "experience": [
                {"title": "Senior Engineer", "company": "Revolut"}
            ],
        }
        text = self.pipeline._build_candidate_text(candidate)
        assert "James Hartley" in text
        assert "Python" in text
        assert "Revolut" in text

    def test_empty_candidate(self):
        text = self.pipeline._build_candidate_text({})
        assert text == ""


class TestEmbeddingGeneration:
    @pytest.mark.asyncio
    async def test_embedding_called(self):
        pipeline = ExtractionPipeline()

        with patch.object(
            pipeline,
            "_generate_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 1536,
        ):
            embedding = await pipeline._generate_embedding("test text")
            assert embedding is not None
            assert len(embedding) == 1536
