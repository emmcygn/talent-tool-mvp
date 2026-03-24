import logging
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from adapters.base import AdapterCandidate
from contracts.shared import (
    AvailabilityStatus,
    CandidateSource,
    ExperienceEntry,
    ExtractedSkill,
    SalaryRange,
    SeniorityLevel,
)

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


def _estimate_seniority(
    title: str | None, years: int | None
) -> SeniorityLevel | None:
    """Estimate seniority from job title and years of experience."""
    if not title:
        if years and years >= 8:
            return SeniorityLevel.senior
        return None

    title_lower = title.lower()
    if any(
        kw in title_lower
        for kw in [
            "principal",
            "staff",
            "distinguished",
            "vp",
            "head of",
            "director",
        ]
    ):
        return SeniorityLevel.principal
    if any(
        kw in title_lower for kw in ["lead", "architect", "engineering manager"]
    ):
        return SeniorityLevel.lead
    if "senior" in title_lower or "sr." in title_lower:
        return SeniorityLevel.senior
    if any(
        kw in title_lower
        for kw in ["junior", "jr.", "graduate", "intern", "associate"]
    ):
        return SeniorityLevel.junior
    # Default to mid if we can't tell
    return SeniorityLevel.mid


def _calculate_experience_months(start: str, end: str | None) -> int | None:
    """Calculate months between two date strings."""
    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = (
            datetime.fromisoformat(end.replace("Z", "+00:00"))
            if end
            else datetime.utcnow()
        )
        delta = end_dt - start_dt
        return max(1, delta.days // 30)
    except (ValueError, TypeError):
        return None


def normalize_bullhorn(record: AdapterCandidate) -> NormalizedCandidate:
    """Normalize a Bullhorn ATS record to canonical format."""
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
        experience.append(
            ExperienceEntry(
                company=job.get("company", "Unknown"),
                title=job.get("title", "Unknown"),
                duration_months=duration,
                industry=None,
            )
        )

    # Parse salary
    salary_data = raw.get("salary")
    salary = None
    if salary_data and salary_data.get("desired"):
        salary = SalaryRange(
            min_amount=Decimal(str(salary_data["desired"])),
            max_amount=Decimal(str(salary_data["desired"])),
            currency=salary_data.get("currency", "GBP"),
        )

    # Determine seniority from most recent title
    current_title = experience[0].title if experience else None
    total_years = (
        sum((e.duration_months or 0) for e in experience) // 12
        if experience
        else None
    )
    seniority = _estimate_seniority(current_title, total_years)

    # Build profile text from employment descriptions
    profile_parts = []
    for job in raw.get("employmentHistory", []):
        desc = job.get("description", "")
        if desc:
            profile_parts.append(
                f"{job.get('title', '')} at {job.get('company', '')}: {desc}"
            )
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
    """Normalize a HubSpot CRM record to canonical format."""
    raw = record.raw_data
    props = raw.get("properties", {})

    # Extract skills from tags
    tags = props.get("tags", [])
    excluded_tags = {
        "london",
        "manchester",
        "bristol",
        "remote",
        "birmingham",
        "cardiff",
        "newcastle",
        "dublin",
        "startup-interested",
        "growth-minded",
        "relocating",
        "relocating-london",
        "lead-aspirant",
        "research-to-industry",
        "founding",
        "fintech-interested",
        "series-a-b",
    }
    skills = [
        ExtractedSkill(name=tag.replace("-", " ").title(), confidence=0.6)
        for tag in tags
        if tag not in excluded_tags
    ]

    # Build single experience entry from current job
    experience = []
    if props.get("company") and props.get("jobtitle"):
        experience.append(
            ExperienceEntry(
                company=props["company"],
                title=props["jobtitle"],
                duration_months=None,
                industry=props.get("industry"),
            )
        )

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
        salary_expectation=None,
        availability=None,
        industries=industries,
        source=CandidateSource(
            adapter_name=record.adapter_name,
            external_id=record.external_id,
            ingested_at=record.fetched_at.isoformat(),
        ),
    )


def normalize_linkedin(record: AdapterCandidate) -> NormalizedCandidate:
    """Normalize a LinkedIn profile record to canonical format."""
    raw = record.raw_data

    # Parse skills with endorsement-based confidence
    max_endorsements = max(
        (s.get("endorsements", 0) for s in raw.get("skills", [])),
        default=1,
    )
    skills = []
    for s in raw.get("skills", []):
        endorsements = s.get("endorsements", 0)
        confidence = 0.5 + (0.5 * endorsements / max(max_endorsements, 1))
        skills.append(
            ExtractedSkill(
                name=s["name"],
                confidence=round(confidence, 2),
            )
        )

    # Parse positions to experience entries
    experience = []
    for pos in raw.get("positions", []):
        experience.append(
            ExperienceEntry(
                company=pos.get("company", "Unknown"),
                title=pos.get("title", "Unknown"),
                duration_months=None,
                industry=None,
            )
        )

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
        parts = location.split(",")
        location = parts[0].strip()

    return NormalizedCandidate(
        first_name=raw.get("firstName", ""),
        last_name=raw.get("lastName", ""),
        email=raw.get("email"),
        phone=None,
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
