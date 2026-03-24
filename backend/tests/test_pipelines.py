from datetime import datetime

import pytest

from adapters.base import AdapterCandidate
from contracts.shared import AvailabilityStatus, SeniorityLevel
from pipelines.normalize import (
    NormalizedCandidate,
    _estimate_seniority,
    _parse_notice_period,
    normalize_bullhorn,
    normalize_candidate,
    normalize_hubspot,
    normalize_linkedin,
)


def _make_adapter_record(adapter_name: str, raw_data: dict) -> AdapterCandidate:
    return AdapterCandidate(
        external_id="TEST-001",
        raw_data=raw_data,
        adapter_name=adapter_name,
        fetched_at=datetime.utcnow(),
    )


class TestNoticeParser:
    def test_immediate(self):
        assert _parse_notice_period("Immediate") == AvailabilityStatus.immediate

    def test_one_month(self):
        assert _parse_notice_period("1 month") == AvailabilityStatus.one_month

    def test_three_months(self):
        assert _parse_notice_period("3 months") == AvailabilityStatus.three_months

    def test_none(self):
        assert _parse_notice_period(None) is None


class TestSeniorityEstimation:
    def test_principal(self):
        assert (
            _estimate_seniority("Staff Software Engineer", None)
            == SeniorityLevel.principal
        )

    def test_lead(self):
        assert (
            _estimate_seniority("Lead Data Engineer", None) == SeniorityLevel.lead
        )

    def test_senior(self):
        assert (
            _estimate_seniority("Senior Backend Engineer", None)
            == SeniorityLevel.senior
        )

    def test_junior(self):
        assert (
            _estimate_seniority("Junior Developer", None) == SeniorityLevel.junior
        )

    def test_mid_default(self):
        assert (
            _estimate_seniority("Software Engineer", None) == SeniorityLevel.mid
        )


class TestBullhornNormalizer:
    def test_basic_fields(self):
        record = _make_adapter_record(
            "bullhorn",
            {
                "candidateId": "BH-1001",
                "firstName": "James",
                "lastName": "Hartley",
                "email": "james@example.com",
                "phone": "+44 7700 100001",
                "address": {"city": "London"},
                "skillList": "Python, FastAPI, PostgreSQL",
                "employmentHistory": [
                    {
                        "company": "Revolut",
                        "title": "Senior Backend Engineer",
                        "startDate": "2021-03-01",
                        "endDate": None,
                        "description": "Led payments team.",
                    },
                ],
                "salary": {"desired": 95000, "currency": "GBP"},
                "noticePeriod": "1 month",
            },
        )
        result = normalize_bullhorn(record)
        assert isinstance(result, NormalizedCandidate)
        assert result.first_name == "James"
        assert result.email == "james@example.com"
        assert result.location == "London"
        assert len(result.skills) == 3
        assert result.skills[0].name == "Python"
        assert len(result.experience) == 1
        assert result.experience[0].company == "Revolut"
        assert result.seniority == SeniorityLevel.senior
        assert result.availability == AvailabilityStatus.one_month
        assert result.salary_expectation is not None
        assert result.source.adapter_name == "bullhorn"

    def test_missing_fields(self):
        """Bullhorn record with minimal data should not error."""
        record = _make_adapter_record(
            "bullhorn",
            {
                "candidateId": "BH-MINIMAL",
                "firstName": "Test",
                "lastName": "User",
            },
        )
        result = normalize_bullhorn(record)
        assert result.first_name == "Test"
        assert result.email is None
        assert result.skills == []
        assert result.experience == []


class TestHubSpotNormalizer:
    def test_basic_fields(self):
        record = _make_adapter_record(
            "hubspot",
            {
                "contactId": "HS-2001",
                "properties": {
                    "firstname": "Aisha",
                    "lastname": "Khan",
                    "email": "aisha@example.com",
                    "city": "London",
                    "jobtitle": "Engineering Manager",
                    "company": "Spotify",
                    "industry": "Technology",
                    "notes": "Managing 3 squads.",
                    "tags": ["management", "engineering-manager", "java"],
                },
            },
        )
        result = normalize_hubspot(record)
        assert result.first_name == "Aisha"
        assert result.location == "London"
        assert len(result.skills) >= 1
        assert len(result.experience) == 1
        assert result.industries == ["Technology"]


class TestLinkedInNormalizer:
    def test_basic_fields(self):
        record = _make_adapter_record(
            "linkedin",
            {
                "profileId": "LI-3001",
                "firstName": "James",
                "lastName": "Hartley",
                "headline": "Senior Backend Engineer at Revolut",
                "location": "London, England, United Kingdom",
                "linkedinUrl": "https://linkedin.com/in/jameshartley-dev",
                "summary": "Building scalable systems.",
                "skills": [
                    {"name": "Python", "endorsements": 42},
                    {"name": "FastAPI", "endorsements": 18},
                ],
                "positions": [
                    {
                        "company": "Revolut",
                        "title": "Senior Backend Engineer",
                        "isCurrent": True,
                    },
                ],
            },
        )
        result = normalize_linkedin(record)
        assert result.first_name == "James"
        assert result.location == "London"
        assert result.linkedin_url == "https://linkedin.com/in/jameshartley-dev"
        assert len(result.skills) == 2
        # Higher endorsements should have higher confidence
        assert result.skills[0].confidence > result.skills[1].confidence


class TestNormalizeDispatch:
    def test_dispatch(self):
        record = _make_adapter_record(
            "bullhorn",
            {
                "candidateId": "BH-TEST",
                "firstName": "Test",
                "lastName": "User",
            },
        )
        result = normalize_candidate(record)
        assert isinstance(result, NormalizedCandidate)

    def test_unknown_adapter(self):
        record = _make_adapter_record("unknown_adapter", {})
        with pytest.raises(KeyError, match="No normalizer"):
            normalize_candidate(record)
