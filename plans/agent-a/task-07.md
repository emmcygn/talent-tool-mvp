# Agent A — Task 07: AI Extraction Pipeline

## Mission
Build the LLM-powered extraction pipeline that uses OpenAI GPT-4o to extract structured candidate data (skills with years, experience, seniority, industries, salary expectations, availability) from CV/profile text. Include confidence scoring per field, embedding generation via text-embedding-3-small, pgvector storage, and flagging of low-confidence fields for human review.

## Context
Day 2 task, depends on Task 03 (FastAPI/config for OpenAI key) and Task 05 (ingestion provides candidates with `profile_text`/`cv_text`). This is the AI enrichment stage — takes raw text and produces structured, queryable data. The extraction runs asynchronously after candidate creation. The embeddings enable semantic search in the matching pipeline (Task 09). Confidence scoring ensures transparency and human-in-the-loop for uncertain extractions.

## Prerequisites
- Task 03 complete (config with `openai_api_key`, `openai_model`, `openai_embedding_model`)
- Task 05 complete (candidates stored with `profile_text` and/or `cv_text`)
- Task 02 complete (candidates table with `embedding vector(1536)`, HNSW index)
- OpenAI API key configured in `.env`

## Checklist
- [ ] Create `backend/pipelines/enrich.py` with `ExtractionPipeline`
- [ ] Implement structured extraction prompt for GPT-4o
- [ ] Parse GPT-4o structured JSON response to canonical fields
- [ ] Implement per-field confidence scoring
- [ ] Flag fields with confidence < 0.7 for human review
- [ ] Implement embedding generation via text-embedding-3-small
- [ ] Store embeddings in pgvector column
- [ ] Update candidate record with extracted data
- [ ] Implement role requirement extraction (reuse similar prompt)
- [ ] Handle API errors gracefully (retry, fallback)
- [ ] Log extraction as signal event
- [ ] Write tests (mock OpenAI responses)
- [ ] Commit

## Implementation Details

### Extraction Pipeline (`backend/pipelines/enrich.py`)

```python
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel
from openai import AsyncOpenAI
from config import settings
from api.deps import get_supabase_admin
from contracts.shared import (
    ExtractedSkill, ExperienceEntry, SeniorityLevel,
    SalaryRange, AvailabilityStatus, SignalType, UserRole,
)
import json
import logging

logger = logging.getLogger("recruittech.pipelines.enrich")

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


class ExtractionResult(BaseModel):
    """Result of AI extraction from candidate text."""
    skills: list[ExtractedSkill] = []
    experience: list[ExperienceEntry] = []
    seniority: SeniorityLevel | None = None
    salary_expectation: SalaryRange | None = None
    availability: AvailabilityStatus | None = None
    industries: list[str] = []
    overall_confidence: float = 0.0
    flagged_fields: list[str] = []
    raw_llm_output: dict = {}
    model_version: str = ""


class RoleExtractionResult(BaseModel):
    """Result of AI extraction from role description."""
    required_skills: list[dict] = []   # {name, min_years, importance}
    preferred_skills: list[dict] = []
    seniority: SeniorityLevel | None = None
    salary_band: SalaryRange | None = None
    industry: str | None = None
    overall_confidence: float = 0.0
    raw_llm_output: dict = {}
    model_version: str = ""


# ---- Extraction Prompts ----

CANDIDATE_EXTRACTION_PROMPT = """You are a recruitment data extraction system. Extract structured information from the following candidate profile/CV text.

Return a JSON object with exactly these fields:

{
  "skills": [
    {"name": "skill name", "years": estimated_years_or_null, "confidence": 0.0_to_1.0}
  ],
  "experience": [
    {"company": "company name", "title": "job title", "duration_months": months_or_null, "industry": "industry_or_null"}
  ],
  "seniority": "junior|mid|senior|lead|principal",
  "salary_expectation": {"min_amount": number_or_null, "max_amount": number_or_null, "currency": "GBP"},
  "availability": "immediate|1_month|3_months|not_looking",
  "industries": ["list", "of", "industries"],
  "field_confidences": {
    "skills": 0.0_to_1.0,
    "experience": 0.0_to_1.0,
    "seniority": 0.0_to_1.0,
    "salary_expectation": 0.0_to_1.0,
    "availability": 0.0_to_1.0,
    "industries": 0.0_to_1.0
  }
}

Rules:
- Confidence scores reflect how certain you are about each extraction (1.0 = explicitly stated, 0.5 = inferred, 0.0 = guessed)
- For skills, estimate years based on work history timeline if not explicitly stated
- Seniority should be inferred from job titles and years of experience
- Salary should only be set if mentioned or strongly implied; otherwise null
- Availability should only be set if mentioned; otherwise null
- All monetary values in GBP
- UK market context — use UK industry categories and terminology
- Return valid JSON only, no markdown formatting"""

ROLE_EXTRACTION_PROMPT = """You are a recruitment data extraction system. Extract structured job requirements from the following role description.

Return a JSON object with exactly these fields:

{
  "required_skills": [
    {"name": "skill name", "min_years": years_or_null, "importance": "required"}
  ],
  "preferred_skills": [
    {"name": "skill name", "min_years": years_or_null, "importance": "preferred"}
  ],
  "seniority": "junior|mid|senior|lead|principal",
  "salary_band": {"min_amount": number_or_null, "max_amount": number_or_null, "currency": "GBP"},
  "industry": "industry name or null",
  "field_confidences": {
    "required_skills": 0.0_to_1.0,
    "preferred_skills": 0.0_to_1.0,
    "seniority": 0.0_to_1.0,
    "salary_band": 0.0_to_1.0,
    "industry": 0.0_to_1.0
  }
}

Rules:
- Distinguish required vs preferred skills based on language ("must have" vs "nice to have")
- Infer minimum years from phrases like "5+ years" or "experienced in"
- UK market context — GBP for salary, UK industry terms
- Return valid JSON only, no markdown formatting"""


class ExtractionPipeline:
    """LLM-powered extraction and embedding generation pipeline.

    Takes raw candidate/role text and produces:
    1. Structured data (skills, experience, seniority, etc.)
    2. Per-field confidence scores
    3. Embedding vector for semantic search

    Usage:
        pipeline = ExtractionPipeline()
        result = await pipeline.extract_candidate(candidate_id)
        result = await pipeline.extract_role(role_id)
    """

    CONFIDENCE_THRESHOLD = 0.7  # fields below this are flagged for review

    async def extract_candidate(self, candidate_id: UUID) -> ExtractionResult:
        """Run AI extraction on a candidate's text data.

        1. Fetch candidate from DB
        2. Send text to GPT-4o for structured extraction
        3. Generate embedding via text-embedding-3-small
        4. Update candidate record with extracted data
        5. Flag low-confidence fields
        6. Emit signal
        """
        supabase = get_supabase_admin()

        # Fetch candidate
        result = supabase.table("candidates").select("*").eq(
            "id", str(candidate_id)
        ).single().execute()
        candidate = result.data

        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        # Build text for extraction
        text = self._build_candidate_text(candidate)
        if not text:
            logger.warning(f"No text available for candidate {candidate_id}")
            return ExtractionResult(overall_confidence=0.0)

        # 1. LLM Extraction
        extraction = await self._call_extraction_llm(
            text, CANDIDATE_EXTRACTION_PROMPT
        )

        # 2. Parse and validate extraction result
        parsed = self._parse_candidate_extraction(extraction)

        # 3. Generate embedding
        embedding = await self._generate_embedding(text)

        # 4. Update candidate record
        await self._update_candidate(
            supabase, candidate_id, parsed, embedding
        )

        # 5. Emit signal
        await self._emit_extraction_signal(
            supabase, candidate_id, candidate.get("created_by"),
            parsed.overall_confidence
        )

        return parsed

    async def extract_role(self, role_id: UUID) -> RoleExtractionResult:
        """Run AI extraction on a role description.

        1. Fetch role from DB
        2. Send description to GPT-4o for requirement extraction
        3. Generate embedding
        4. Update role record
        """
        supabase = get_supabase_admin()

        result = supabase.table("roles").select("*").eq(
            "id", str(role_id)
        ).single().execute()
        role = result.data

        if not role:
            raise ValueError(f"Role {role_id} not found")

        text = f"{role.get('title', '')}\n\n{role.get('description', '')}"

        # 1. LLM Extraction
        extraction = await self._call_extraction_llm(
            text, ROLE_EXTRACTION_PROMPT
        )

        # 2. Parse role extraction
        parsed = self._parse_role_extraction(extraction)

        # 3. Generate embedding
        embedding = await self._generate_embedding(text)

        # 4. Update role record
        update_data = {
            "required_skills": parsed.required_skills,
            "preferred_skills": parsed.preferred_skills,
            "seniority": parsed.seniority.value if parsed.seniority else None,
            "salary_band": (
                parsed.salary_band.model_dump(mode="json")
                if parsed.salary_band else None
            ),
            "industry": parsed.industry,
            "extraction_confidence": parsed.overall_confidence,
            "embedding": embedding,
        }
        supabase.table("roles").update(update_data).eq(
            "id", str(role_id)
        ).execute()

        return parsed

    async def _call_extraction_llm(
        self,
        text: str,
        system_prompt: str,
    ) -> dict:
        """Call GPT-4o for structured extraction.

        Uses JSON mode for reliable structured output.
        Retries once on failure.
        """
        for attempt in range(2):
            try:
                response = await openai_client.chat.completions.create(
                    model=settings.openai_model,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text},
                    ],
                    temperature=0.1,  # low temperature for consistent extraction
                    max_tokens=2000,
                )

                content = response.choices[0].message.content
                return json.loads(content)

            except json.JSONDecodeError as e:
                logger.warning(f"LLM returned invalid JSON (attempt {attempt + 1}): {e}")
                if attempt == 1:
                    return {}
            except Exception as e:
                logger.error(f"LLM extraction failed (attempt {attempt + 1}): {e}")
                if attempt == 1:
                    return {}

        return {}

    async def _generate_embedding(self, text: str) -> list[float] | None:
        """Generate embedding via text-embedding-3-small.

        Truncates text to ~8000 tokens to stay within model limits.
        """
        if not text:
            return None

        # Rough truncation (1 token ~ 4 chars for English)
        max_chars = 32000
        truncated = text[:max_chars]

        try:
            response = await openai_client.embeddings.create(
                model=settings.openai_embedding_model,
                input=truncated,
                dimensions=settings.embedding_dimensions,
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    def _build_candidate_text(self, candidate: dict) -> str:
        """Build text for extraction from all available candidate data."""
        parts = []

        if candidate.get("cv_text"):
            parts.append(candidate["cv_text"])

        if candidate.get("profile_text"):
            parts.append(candidate["profile_text"])

        # Fallback: build text from structured data already present
        if not parts:
            name = f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}".strip()
            if name:
                parts.append(f"Name: {name}")

            skills = candidate.get("skills", [])
            if skills:
                skill_names = [s.get("name", "") for s in skills if s.get("name")]
                if skill_names:
                    parts.append(f"Skills: {', '.join(skill_names)}")

            experience = candidate.get("experience", [])
            for exp in experience:
                title = exp.get("title", "")
                company = exp.get("company", "")
                if title and company:
                    parts.append(f"{title} at {company}")

        return "\n\n".join(parts)

    def _parse_candidate_extraction(self, raw: dict) -> ExtractionResult:
        """Parse LLM output into ExtractionResult with confidence scoring."""
        if not raw:
            return ExtractionResult(overall_confidence=0.0)

        field_confidences = raw.get("field_confidences", {})
        flagged_fields = []

        # Parse skills
        skills = []
        for s in raw.get("skills", []):
            skills.append(ExtractedSkill(
                name=s.get("name", ""),
                years=s.get("years"),
                confidence=s.get("confidence", 0.5),
            ))

        # Parse experience
        experience = []
        for e in raw.get("experience", []):
            experience.append(ExperienceEntry(
                company=e.get("company", ""),
                title=e.get("title", ""),
                duration_months=e.get("duration_months"),
                industry=e.get("industry"),
            ))

        # Parse seniority
        seniority = None
        seniority_str = raw.get("seniority")
        if seniority_str:
            try:
                seniority = SeniorityLevel(seniority_str)
            except ValueError:
                logger.warning(f"Invalid seniority: {seniority_str}")

        # Parse salary
        salary = None
        salary_raw = raw.get("salary_expectation")
        if salary_raw and (salary_raw.get("min_amount") or salary_raw.get("max_amount")):
            from decimal import Decimal
            salary = SalaryRange(
                min_amount=Decimal(str(salary_raw["min_amount"])) if salary_raw.get("min_amount") else None,
                max_amount=Decimal(str(salary_raw["max_amount"])) if salary_raw.get("max_amount") else None,
                currency=salary_raw.get("currency", "GBP"),
            )

        # Parse availability
        availability = None
        avail_str = raw.get("availability")
        if avail_str:
            try:
                availability = AvailabilityStatus(avail_str)
            except ValueError:
                logger.warning(f"Invalid availability: {avail_str}")

        # Parse industries
        industries = raw.get("industries", [])

        # Compute overall confidence and flag low-confidence fields
        all_confidences = []
        for field_name, conf in field_confidences.items():
            all_confidences.append(conf)
            if conf < self.CONFIDENCE_THRESHOLD:
                flagged_fields.append(field_name)

        overall_confidence = (
            sum(all_confidences) / len(all_confidences)
            if all_confidences else 0.0
        )

        return ExtractionResult(
            skills=skills,
            experience=experience,
            seniority=seniority,
            salary_expectation=salary,
            availability=availability,
            industries=industries,
            overall_confidence=round(overall_confidence, 3),
            flagged_fields=flagged_fields,
            raw_llm_output=raw,
            model_version=settings.openai_model,
        )

    def _parse_role_extraction(self, raw: dict) -> RoleExtractionResult:
        """Parse LLM output for role requirement extraction."""
        if not raw:
            return RoleExtractionResult(overall_confidence=0.0)

        field_confidences = raw.get("field_confidences", {})

        # Parse seniority
        seniority = None
        seniority_str = raw.get("seniority")
        if seniority_str:
            try:
                seniority = SeniorityLevel(seniority_str)
            except ValueError:
                pass

        # Parse salary band
        salary_band = None
        salary_raw = raw.get("salary_band")
        if salary_raw and (salary_raw.get("min_amount") or salary_raw.get("max_amount")):
            from decimal import Decimal
            salary_band = SalaryRange(
                min_amount=Decimal(str(salary_raw["min_amount"])) if salary_raw.get("min_amount") else None,
                max_amount=Decimal(str(salary_raw["max_amount"])) if salary_raw.get("max_amount") else None,
                currency=salary_raw.get("currency", "GBP"),
            )

        # Compute confidence
        all_confidences = list(field_confidences.values())
        overall_confidence = (
            sum(all_confidences) / len(all_confidences)
            if all_confidences else 0.0
        )

        return RoleExtractionResult(
            required_skills=raw.get("required_skills", []),
            preferred_skills=raw.get("preferred_skills", []),
            seniority=seniority,
            salary_band=salary_band,
            industry=raw.get("industry"),
            overall_confidence=round(overall_confidence, 3),
            raw_llm_output=raw,
            model_version=settings.openai_model,
        )

    async def _update_candidate(
        self,
        supabase,
        candidate_id: UUID,
        extraction: ExtractionResult,
        embedding: list[float] | None,
    ) -> None:
        """Update candidate record with extracted data and embedding."""
        update_data = {
            "skills": [s.model_dump() for s in extraction.skills],
            "experience": [e.model_dump() for e in extraction.experience],
            "seniority": extraction.seniority.value if extraction.seniority else None,
            "salary_expectation": (
                extraction.salary_expectation.model_dump(mode="json")
                if extraction.salary_expectation else None
            ),
            "availability": (
                extraction.availability.value if extraction.availability else None
            ),
            "industries": extraction.industries,
            "extraction_confidence": extraction.overall_confidence,
            "extraction_flags": extraction.flagged_fields,
            "embedding": embedding,
        }

        supabase.table("candidates").update(update_data).eq(
            "id", str(candidate_id)
        ).execute()

        logger.info(
            f"Updated candidate {candidate_id}: "
            f"confidence={extraction.overall_confidence:.2f}, "
            f"flags={extraction.flagged_fields}, "
            f"skills={len(extraction.skills)}, "
            f"embedding={'yes' if embedding else 'no'}"
        )

    async def _emit_extraction_signal(
        self,
        supabase,
        candidate_id: UUID,
        user_id: str | None,
        confidence: float,
    ) -> None:
        """Emit signal for candidate extraction completion."""
        signal = {
            "id": str(uuid4()),
            "event_type": SignalType.candidate_ingested.value,
            "actor_id": user_id or str(uuid4()),
            "actor_role": UserRole.talent_partner.value,
            "entity_type": "candidate",
            "entity_id": str(candidate_id),
            "metadata": {
                "event_subtype": "extraction_completed",
                "extraction_confidence": confidence,
                "model_version": settings.openai_model,
            },
        }
        try:
            supabase.table("signals").insert(signal).execute()
        except Exception as e:
            logger.warning(f"Failed to emit extraction signal: {e}")
```

### Tests (`backend/tests/test_enrich.py`)

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from pipelines.enrich import (
    ExtractionPipeline,
    ExtractionResult,
    RoleExtractionResult,
    CANDIDATE_EXTRACTION_PROMPT,
    ROLE_EXTRACTION_PROMPT,
)
from contracts.shared import SeniorityLevel, AvailabilityStatus


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
        {"company": "Revolut", "title": "Senior Backend Engineer", "duration_months": 36, "industry": "Fintech"},
        {"company": "Monzo", "title": "Backend Engineer", "duration_months": 33, "industry": "Fintech"},
        {"company": "ThoughtWorks", "title": "Software Consultant", "duration_months": 29, "industry": "Consulting"},
    ],
    "seniority": "senior",
    "salary_expectation": {"min_amount": 90000, "max_amount": 100000, "currency": "GBP"},
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
    "salary_band": {"min_amount": 80000, "max_amount": 100000, "currency": "GBP"},
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
        result = self.pipeline._parse_candidate_extraction(MOCK_CANDIDATE_LLM_RESPONSE)
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
        result = self.pipeline._parse_candidate_extraction(MOCK_CANDIDATE_LLM_RESPONSE)
        # salary_expectation has confidence 0.60, below threshold 0.7
        assert "salary_expectation" in result.flagged_fields

    def test_high_confidence_not_flagged(self):
        result = self.pipeline._parse_candidate_extraction(MOCK_CANDIDATE_LLM_RESPONSE)
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
            "experience": [{"title": "Senior Engineer", "company": "Revolut"}],
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
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]

        with patch.object(
            pipeline, "_generate_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 1536,
        ) as mock_embed:
            embedding = await pipeline._generate_embedding("test text")
            assert embedding is not None
            assert len(embedding) == 1536
```

## Outputs
- `backend/pipelines/enrich.py`
- `backend/tests/test_enrich.py`

## Acceptance Criteria
1. `ExtractionPipeline.extract_candidate()` calls GPT-4o with structured prompt, parses response
2. Extraction returns skills with name, years, and per-skill confidence
3. Experience entries include company, title, duration, industry
4. Seniority, salary, availability correctly parsed from LLM output
5. Fields with confidence < 0.7 are added to `extraction_flags`
6. Embedding generated via text-embedding-3-small (1536 dimensions)
7. Candidate record updated in Supabase with extracted data + embedding
8. `ExtractionPipeline.extract_role()` extracts requirements from role description
9. Empty/invalid LLM responses handled gracefully (no crash, returns defaults)
10. Signal emitted for each extraction
11. `python -m pytest tests/test_enrich.py -v` — all tests pass

## Handoff Notes
- **To Task 08:** Candidate creation should trigger `ExtractionPipeline.extract_candidate(candidate_id)` asynchronously after insert. Role creation should trigger `extract_role(role_id)`. Import as `from pipelines.enrich import ExtractionPipeline`.
- **To Task 09:** Embeddings are stored in the `embedding` column on both `candidates` and `roles` tables. Use pgvector's `<=>` operator for cosine distance in semantic matching. HNSW index is already created in Task 02.
- **To Agent B:** Extraction confidence and flagged fields are returned on the candidate object. Fields in `extraction_flags` should be highlighted amber in the UI for human review. The `extraction_confidence` is the overall confidence score (0-1).
- **Decision:** Using `response_format={"type": "json_object"}` for reliable JSON output from GPT-4o. Temperature set to 0.1 for consistent extractions.
- **Decision:** Embedding text is built from CV + profile text. Falls back to structured data (skills list, experience) if no raw text exists. This ensures every candidate gets an embedding even if they only have adapter-extracted data.
- **Decision:** LLM calls retry once on failure. If both attempts fail, returns empty result with 0.0 confidence. The candidate is still stored — just without AI extraction.
