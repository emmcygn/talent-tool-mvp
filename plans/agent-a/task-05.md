# Agent A — Task 05: Ingest + Normalize Pipeline

## Mission
Build the ingestion service that pulls raw candidate records from adapters and the normalization step that maps adapter-specific fields to the canonical `Candidate` format. Store normalized candidates in Supabase. Handle partial/missing data gracefully. Log each ingestion as a signal event.

## Context
Day 2 task, depends on Task 02 (schema) and Task 04 (adapters). This is the first half of the ETL pipeline. Raw adapter data has different field names, structures, and completeness levels. The normalizer must handle all three adapter formats (Bullhorn ATS, HubSpot CRM, LinkedIn profiles) and produce consistent canonical `Candidate` records. Missing fields should be `None`, not errors.

## Prerequisites
- Task 02 complete (database schema with candidates table)
- Task 04 complete (adapters with mock data)
- Task 01 complete (canonical contracts)
- Supabase running locally

## Checklist
- [ ] Create `backend/pipelines/__init__.py`
- [ ] Create `backend/pipelines/ingest.py` with `IngestionService`
- [ ] Create `backend/pipelines/normalize.py` with normalizer per adapter
- [ ] Implement Bullhorn normalizer (parses `skillList` string, `employmentHistory` array, `salary` object)
- [ ] Implement HubSpot normalizer (parses `properties` object, `tags`, `notes`)
- [ ] Implement LinkedIn normalizer (parses `skills` with endorsements, `positions`, `summary`)
- [ ] Handle missing/partial data — every field defaults gracefully
- [ ] Map notice period strings to `AvailabilityStatus` enum
- [ ] Store normalized candidates in Supabase `candidates` table
- [ ] Emit `candidate_ingested` signal for each ingested candidate
- [ ] Create ingestion result summary (counts, errors, duplicates found)
- [ ] Write tests for each normalizer
- [ ] Commit

## Implementation Details

### Normalizer (`backend/pipelines/normalize.py`)

```python
from datetime import datetime
from contracts.shared import (
    ExtractedSkill, ExperienceEntry, SeniorityLevel,
    SalaryRange, AvailabilityStatus, CandidateSource,
)
from contracts.candidate import CandidateCreate
from adapters.base import AdapterCandidate
from pydantic import BaseModel
import logging
import re

logger = logging.getLogger("recruittech.pipelines.normalize")


class NormalizedCandidate(BaseModel):
    """Result of normalizing an adapter record to canonical format.

    Contains the CandidateCreate data plus extracted structured fields
    that come from the raw adapter data (not yet LLM-extracted).
    """
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    cv_text: str | None = None
    profile_text: str | None = None

    # Pre-extracted from adapter data (basic, non-LLM extraction)
    skills: list[ExtractedSkill] = []
    experience: list[ExperienceEntry] = []
    seniority: SeniorityLevel | None = None
    salary_expectation: SalaryRange | None = None
    availability: AvailabilityStatus | None = None
    industries: list[str] = []

    # Source tracking
    source: CandidateSource


def _parse_notice_period(notice: str | None) -> AvailabilityStatus | None:
    """Map notice period strings to AvailabilityStatus enum."""
    if not notice:
        return None
    notice = notice.lower().strip()
    if "immediate" in notice or "now" in notice:
        return AvailabilityStatus.immediate
    if "1 month" in notice or "one month" in notice or "4 week" in notice:
        return AvailabilityStatus.one_month
    if "3 month" in notice or "three month" in notice or "12 week" in notice:
        return AvailabilityStatus.three_months
    if "not looking" in notice or "not available" in notice:
        return AvailabilityStatus.not_looking
    return AvailabilityStatus.one_month  # safe default


def _estimate_seniority(title: str | None, years: int | None) -> SeniorityLevel | None:
    """Estimate seniority from job title and years of experience."""
    if not title:
        if years and years >= 8:
            return SeniorityLevel.senior
        return None

    title_lower = title.lower()
    if any(kw in title_lower for kw in ["principal", "staff", "distinguished", "vp", "head of", "director"]):
        return SeniorityLevel.principal
    if any(kw in title_lower for kw in ["lead", "architect", "engineering manager"]):
        return SeniorityLevel.lead
    if "senior" in title_lower or "sr." in title_lower:
        return SeniorityLevel.senior
    if any(kw in title_lower for kw in ["junior", "jr.", "graduate", "intern", "associate"]):
        return SeniorityLevel.junior
    # Default to mid if we can't tell
    return SeniorityLevel.mid


def _calculate_experience_months(start: str, end: str | None) -> int | None:
    """Calculate months between two date strings."""
    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00")) if end else datetime.utcnow()
        delta = end_dt - start_dt
        return max(1, delta.days // 30)
    except (ValueError, TypeError):
        return None


def normalize_bullhorn(record: AdapterCandidate) -> NormalizedCandidate:
    """Normalize a Bullhorn ATS record to canonical format.

    Bullhorn provides:
    - skillList as comma-separated string
    - employmentHistory as array with dates
    - salary as {desired, currency}
    - noticePeriod as text
    - address as {city, postcode}
    """
    raw = record.raw_data
    address = raw.get("address", {})

    # Parse comma-separated skills
    skill_str = raw.get("skillList", "")
    skills = [
        ExtractedSkill(name=s.strip(), confidence=0.8)
        for s in skill_str.split(",")
        if s.strip()
    ]

    # Parse employment history
    experience = []
    for job in raw.get("employmentHistory", []):
        duration = _calculate_experience_months(
            job.get("startDate", ""),
            job.get("endDate"),
        )
        experience.append(ExperienceEntry(
            company=job.get("company", "Unknown"),
            title=job.get("title", "Unknown"),
            duration_months=duration,
            industry=None,  # Bullhorn doesn't always tag industry per job
        ))

    # Parse salary
    salary_data = raw.get("salary")
    salary = None
    if salary_data and salary_data.get("desired"):
        from decimal import Decimal
        salary = SalaryRange(
            min_amount=Decimal(str(salary_data["desired"])),
            max_amount=Decimal(str(salary_data["desired"])),
            currency=salary_data.get("currency", "GBP"),
        )

    # Determine seniority from most recent title
    current_title = experience[0].title if experience else None
    total_years = sum((e.duration_months or 0) for e in experience) // 12 if experience else None
    seniority = _estimate_seniority(current_title, total_years)

    # Build profile text from employment descriptions
    profile_parts = []
    for job in raw.get("employmentHistory", []):
        desc = job.get("description", "")
        if desc:
            profile_parts.append(f"{job.get('title', '')} at {job.get('company', '')}: {desc}")
    profile_text = "\n".join(profile_parts) if profile_parts else None

    return NormalizedCandidate(
        first_name=raw.get("firstName", ""),
        last_name=raw.get("lastName", ""),
        email=raw.get("email"),
        phone=raw.get("phone"),
        location=address.get("city"),
        linkedin_url=None,
        cv_text=None,
        profile_text=profile_text,
        skills=skills,
        experience=experience,
        seniority=seniority,
        salary_expectation=salary,
        availability=_parse_notice_period(raw.get("noticePeriod")),
        industries=[],
        source=CandidateSource(
            adapter_name=record.adapter_name,
            external_id=record.external_id,
            ingested_at=record.fetched_at.isoformat(),
        ),
    )


def normalize_hubspot(record: AdapterCandidate) -> NormalizedCandidate:
    """Normalize a HubSpot CRM record to canonical format.

    HubSpot provides:
    - properties object with flat fields
    - tags as array
    - notes as free text (contains useful info)
    - engagement_score as number
    - Less structured work history
    """
    raw = record.raw_data
    props = raw.get("properties", {})

    # Extract skills from tags
    tags = props.get("tags", [])
    skills = [
        ExtractedSkill(name=tag.replace("-", " ").title(), confidence=0.6)
        for tag in tags
        if tag not in ("london", "manchester", "bristol", "remote",
                       "birmingham", "cardiff", "newcastle", "dublin",
                       "startup-interested", "growth-minded", "relocating",
                       "relocating-london", "lead-aspirant",
                       "research-to-industry", "founding",
                       "fintech-interested", "series-a-b")
    ]

    # Build single experience entry from current job
    experience = []
    if props.get("company") and props.get("jobtitle"):
        experience.append(ExperienceEntry(
            company=props["company"],
            title=props["jobtitle"],
            duration_months=None,
            industry=props.get("industry"),
        ))

    # Industry from properties
    industries = [props["industry"]] if props.get("industry") else []

    # Seniority from job title
    seniority = _estimate_seniority(props.get("jobtitle"), None)

    # Profile text from notes
    profile_text = props.get("notes")

    return NormalizedCandidate(
        first_name=props.get("firstname", ""),
        last_name=props.get("lastname", ""),
        email=props.get("email"),
        phone=props.get("phone"),
        location=props.get("city"),
        linkedin_url=None,
        cv_text=None,
        profile_text=profile_text,
        skills=skills,
        experience=experience,
        seniority=seniority,
        salary_expectation=None,  # HubSpot CRM typically doesn't track salary
        availability=None,  # Not tracked in CRM
        industries=industries,
        source=CandidateSource(
            adapter_name=record.adapter_name,
            external_id=record.external_id,
            ingested_at=record.fetched_at.isoformat(),
        ),
    )


def normalize_linkedin(record: AdapterCandidate) -> NormalizedCandidate:
    """Normalize a LinkedIn profile record to canonical format.

    LinkedIn provides:
    - skills with endorsement counts (higher endorsements = higher confidence)
    - positions with company/title (no dates usually)
    - summary as profile text
    - education details
    - headline
    """
    raw = record.raw_data

    # Parse skills with endorsement-based confidence
    max_endorsements = max(
        (s.get("endorsements", 0) for s in raw.get("skills", [])),
        default=1,
    )
    skills = []
    for s in raw.get("skills", []):
        endorsements = s.get("endorsements", 0)
        # Scale confidence: 0.5 base + up to 0.5 based on relative endorsements
        confidence = 0.5 + (0.5 * endorsements / max(max_endorsements, 1))
        skills.append(ExtractedSkill(
            name=s["name"],
            confidence=round(confidence, 2),
        ))

    # Parse positions to experience entries
    experience = []
    for pos in raw.get("positions", []):
        experience.append(ExperienceEntry(
            company=pos.get("company", "Unknown"),
            title=pos.get("title", "Unknown"),
            duration_months=None,  # LinkedIn mock doesn't have dates
            industry=None,
        ))

    # Seniority from current position headline
    current_title = experience[0].title if experience else None
    seniority = _estimate_seniority(current_title, None)

    # Build profile text from headline + summary
    profile_parts = []
    if raw.get("headline"):
        profile_parts.append(raw["headline"])
    if raw.get("summary"):
        profile_parts.append(raw["summary"])
    profile_text = "\n\n".join(profile_parts) if profile_parts else None

    # Parse location — LinkedIn uses "City, Country" format
    location = raw.get("location")
    if location:
        # Extract just city from "London, England, United Kingdom"
        parts = location.split(",")
        location = parts[0].strip()

    return NormalizedCandidate(
        first_name=raw.get("firstName", ""),
        last_name=raw.get("lastName", ""),
        email=raw.get("email"),
        phone=None,  # LinkedIn rarely shares phone
        location=location,
        linkedin_url=raw.get("linkedinUrl"),
        cv_text=None,
        profile_text=profile_text,
        skills=skills,
        experience=experience,
        seniority=seniority,
        salary_expectation=None,
        availability=None,
        industries=[],
        source=CandidateSource(
            adapter_name=record.adapter_name,
            external_id=record.external_id,
            ingested_at=record.fetched_at.isoformat(),
        ),
    )


# Normalizer dispatch table
NORMALIZERS = {
    "bullhorn": normalize_bullhorn,
    "hubspot": normalize_hubspot,
    "linkedin": normalize_linkedin,
}


def normalize_candidate(record: AdapterCandidate) -> NormalizedCandidate:
    """Normalize any adapter record to canonical format.

    Dispatches to the appropriate normalizer based on adapter_name.
    Raises KeyError if adapter is unknown.
    """
    normalizer = NORMALIZERS.get(record.adapter_name)
    if not normalizer:
        raise KeyError(
            f"No normalizer for adapter '{record.adapter_name}'. "
            f"Available: {list(NORMALIZERS.keys())}"
        )
    return normalizer(record)
```

### Ingestion Service (`backend/pipelines/ingest.py`)

```python
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel
from adapters.base import BaseAdapter, AdapterCandidate
from adapters.registry import adapter_registry
from pipelines.normalize import normalize_candidate, NormalizedCandidate
from contracts.shared import SignalType, UserRole
from api.deps import get_supabase_admin
import logging

logger = logging.getLogger("recruittech.pipelines.ingest")


class IngestionResult(BaseModel):
    """Summary of an ingestion run."""
    adapter_name: str
    total_fetched: int
    total_normalized: int
    total_stored: int
    total_errors: int
    errors: list[str] = []
    started_at: datetime
    completed_at: datetime


class IngestionService:
    """Orchestrates pulling data from adapters, normalizing, and storing.

    Usage:
        service = IngestionService()
        result = await service.ingest_from_adapter("bullhorn", user_id=...)
        result = await service.ingest_all(user_id=...)
    """

    async def ingest_from_adapter(
        self,
        adapter_name: str,
        user_id: UUID,
        since: datetime | None = None,
        limit: int = 100,
    ) -> IngestionResult:
        """Ingest candidates from a single adapter.

        Args:
            adapter_name: Adapter to pull from (e.g., "bullhorn")
            user_id: Talent partner performing the ingestion
            since: Only fetch records modified after this time
            limit: Maximum records to fetch
        """
        started_at = datetime.utcnow()
        errors: list[str] = []

        # 1. Fetch from adapter
        adapter = adapter_registry.get(adapter_name)
        raw_records = await adapter.fetch_candidates(since=since, limit=limit)
        logger.info(f"Fetched {len(raw_records)} records from {adapter_name}")

        # 2. Normalize each record
        normalized: list[NormalizedCandidate] = []
        for record in raw_records:
            try:
                norm = normalize_candidate(record)
                normalized.append(norm)
            except Exception as e:
                error_msg = f"Normalization failed for {record.external_id}: {e}"
                logger.warning(error_msg)
                errors.append(error_msg)

        logger.info(f"Normalized {len(normalized)}/{len(raw_records)} records")

        # 3. Store in Supabase
        stored_count = 0
        supabase = get_supabase_admin()
        for norm in normalized:
            try:
                await self._store_candidate(supabase, norm, user_id)
                stored_count += 1

                # 4. Emit signal for each ingestion
                await self._emit_ingestion_signal(
                    supabase, user_id, norm.source.adapter_name, norm.email
                )
            except Exception as e:
                error_msg = f"Storage failed for {norm.first_name} {norm.last_name}: {e}"
                logger.warning(error_msg)
                errors.append(error_msg)

        completed_at = datetime.utcnow()
        logger.info(
            f"Ingestion complete: {adapter_name} — "
            f"{stored_count} stored, {len(errors)} errors"
        )

        return IngestionResult(
            adapter_name=adapter_name,
            total_fetched=len(raw_records),
            total_normalized=len(normalized),
            total_stored=stored_count,
            total_errors=len(errors),
            errors=errors,
            started_at=started_at,
            completed_at=completed_at,
        )

    async def ingest_all(
        self,
        user_id: UUID,
        since: datetime | None = None,
    ) -> list[IngestionResult]:
        """Ingest candidates from all registered adapters."""
        results = []
        for adapter_name in adapter_registry.list_names():
            result = await self.ingest_from_adapter(
                adapter_name=adapter_name,
                user_id=user_id,
                since=since,
            )
            results.append(result)
        return results

    async def _store_candidate(
        self,
        supabase,
        candidate: NormalizedCandidate,
        user_id: UUID,
    ) -> dict:
        """Store a normalized candidate in the candidates table.

        Converts Pydantic models to JSON-serializable dicts for JSONB columns.
        """
        record = {
            "id": str(uuid4()),
            "first_name": candidate.first_name,
            "last_name": candidate.last_name,
            "email": candidate.email,
            "phone": candidate.phone,
            "location": candidate.location,
            "linkedin_url": candidate.linkedin_url,
            "cv_text": candidate.cv_text,
            "profile_text": candidate.profile_text,
            "skills": [s.model_dump() for s in candidate.skills],
            "experience": [e.model_dump() for e in candidate.experience],
            "seniority": candidate.seniority.value if candidate.seniority else None,
            "salary_expectation": (
                candidate.salary_expectation.model_dump(mode="json")
                if candidate.salary_expectation else None
            ),
            "availability": (
                candidate.availability.value if candidate.availability else None
            ),
            "industries": candidate.industries,
            "sources": [candidate.source.model_dump()],
            "extraction_confidence": None,  # Set by AI extraction pipeline (Task 07)
            "extraction_flags": [],
            "created_by": str(user_id),
        }

        result = supabase.table("candidates").insert(record).execute()
        return result.data[0] if result.data else {}

    async def _emit_ingestion_signal(
        self,
        supabase,
        user_id: UUID,
        adapter_name: str,
        candidate_email: str | None,
    ) -> None:
        """Emit a candidate_ingested signal event."""
        signal = {
            "id": str(uuid4()),
            "event_type": SignalType.candidate_ingested.value,
            "actor_id": str(user_id),
            "actor_role": UserRole.talent_partner.value,
            "entity_type": "candidate",
            "entity_id": str(uuid4()),  # TODO: use actual candidate ID after insert
            "metadata": {
                "adapter_name": adapter_name,
                "candidate_email": candidate_email,
            },
        }
        try:
            supabase.table("signals").insert(signal).execute()
        except Exception as e:
            # Don't fail ingestion if signal emission fails
            logger.warning(f"Failed to emit ingestion signal: {e}")
```

### Tests (`backend/tests/test_pipelines.py`)

```python
import pytest
from datetime import datetime
from pipelines.normalize import (
    normalize_bullhorn, normalize_hubspot, normalize_linkedin,
    normalize_candidate, NormalizedCandidate,
    _parse_notice_period, _estimate_seniority,
)
from adapters.base import AdapterCandidate
from contracts.shared import AvailabilityStatus, SeniorityLevel


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
        assert _estimate_seniority("Staff Software Engineer", None) == SeniorityLevel.principal

    def test_lead(self):
        assert _estimate_seniority("Lead Data Engineer", None) == SeniorityLevel.lead

    def test_senior(self):
        assert _estimate_seniority("Senior Backend Engineer", None) == SeniorityLevel.senior

    def test_junior(self):
        assert _estimate_seniority("Junior Developer", None) == SeniorityLevel.junior

    def test_mid_default(self):
        assert _estimate_seniority("Software Engineer", None) == SeniorityLevel.mid


class TestBullhornNormalizer:
    def test_basic_fields(self):
        record = _make_adapter_record("bullhorn", {
            "candidateId": "BH-1001",
            "firstName": "James",
            "lastName": "Hartley",
            "email": "james@example.com",
            "phone": "+44 7700 100001",
            "address": {"city": "London"},
            "skillList": "Python, FastAPI, PostgreSQL",
            "employmentHistory": [
                {"company": "Revolut", "title": "Senior Backend Engineer",
                 "startDate": "2021-03-01", "endDate": None,
                 "description": "Led payments team."},
            ],
            "salary": {"desired": 95000, "currency": "GBP"},
            "noticePeriod": "1 month",
        })
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
        record = _make_adapter_record("bullhorn", {
            "candidateId": "BH-MINIMAL",
            "firstName": "Test",
            "lastName": "User",
        })
        result = normalize_bullhorn(record)
        assert result.first_name == "Test"
        assert result.email is None
        assert result.skills == []
        assert result.experience == []


class TestHubSpotNormalizer:
    def test_basic_fields(self):
        record = _make_adapter_record("hubspot", {
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
        })
        result = normalize_hubspot(record)
        assert result.first_name == "Aisha"
        assert result.location == "London"
        assert len(result.skills) >= 1
        assert len(result.experience) == 1
        assert result.industries == ["Technology"]


class TestLinkedInNormalizer:
    def test_basic_fields(self):
        record = _make_adapter_record("linkedin", {
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
                {"company": "Revolut", "title": "Senior Backend Engineer", "isCurrent": True},
            ],
        })
        result = normalize_linkedin(record)
        assert result.first_name == "James"
        assert result.location == "London"
        assert result.linkedin_url == "https://linkedin.com/in/jameshartley-dev"
        assert len(result.skills) == 2
        # Higher endorsements should have higher confidence
        assert result.skills[0].confidence > result.skills[1].confidence


class TestNormalizeDispatch:
    def test_dispatch(self):
        record = _make_adapter_record("bullhorn", {
            "candidateId": "BH-TEST",
            "firstName": "Test",
            "lastName": "User",
        })
        result = normalize_candidate(record)
        assert isinstance(result, NormalizedCandidate)

    def test_unknown_adapter(self):
        record = _make_adapter_record("unknown_adapter", {})
        with pytest.raises(KeyError, match="No normalizer"):
            normalize_candidate(record)
```

## Outputs
- `backend/pipelines/__init__.py`
- `backend/pipelines/ingest.py`
- `backend/pipelines/normalize.py`
- `backend/tests/test_pipelines.py`

## Acceptance Criteria
1. All three normalizers correctly map adapter-specific fields to `NormalizedCandidate`
2. Missing/partial data produces `None` values, not exceptions
3. Bullhorn: comma-separated `skillList` parsed to list of `ExtractedSkill`
4. HubSpot: CRM tags converted to skills (excluding location/status tags)
5. LinkedIn: endorsement counts mapped to skill confidence scores
6. Notice period strings correctly mapped to `AvailabilityStatus` enum
7. Job titles correctly mapped to `SeniorityLevel` enum
8. `IngestionService.ingest_from_adapter()` returns `IngestionResult` with counts
9. Each ingestion emits a `candidate_ingested` signal
10. `python -m pytest tests/test_pipelines.py -v` — all tests pass

## Handoff Notes
- **To Task 06:** Normalized candidates are stored with `sources` array containing the adapter source. The dedup pipeline should check for existing candidates by email/phone before inserting and merge sources when duplicates are found.
- **To Task 07:** Normalized candidates have basic skill extraction from adapter data (confidence 0.6-0.8). The AI extraction pipeline should re-extract from `profile_text` and `cv_text` for higher-confidence structured data, then update the candidate record.
- **To Task 08:** The `IngestionService` is called from API endpoints when a talent partner triggers a sync. Import as `from pipelines.ingest import IngestionService`.
- **Decision:** Normalization is synchronous and deterministic (no LLM calls). LLM extraction happens in Task 07 as a separate pipeline stage. This keeps ingestion fast and testable.
- **Decision:** Each adapter's normalizer is a standalone function, not a method on the adapter class. This keeps adapters focused on data fetching and normalizers focused on field mapping.
