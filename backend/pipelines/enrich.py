import json
import logging
from decimal import Decimal
from uuid import UUID, uuid4

from openai import AsyncOpenAI
from pydantic import BaseModel

from api.deps import get_supabase_admin
from config import settings
from contracts.shared import (
    AvailabilityStatus,
    ExperienceEntry,
    ExtractedSkill,
    SalaryRange,
    SeniorityLevel,
    SignalType,
    UserRole,
)

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

    required_skills: list[dict] = []
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
    """LLM-powered extraction and embedding generation pipeline."""

    CONFIDENCE_THRESHOLD = 0.7

    async def extract_candidate(self, candidate_id: UUID) -> ExtractionResult:
        """Run AI extraction on a candidate's text data."""
        supabase = get_supabase_admin()

        result = (
            supabase.table("candidates")
            .select("*")
            .eq("id", str(candidate_id))
            .single()
            .execute()
        )
        candidate = result.data

        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        text = self._build_candidate_text(candidate)
        if not text:
            logger.warning(f"No text available for candidate {candidate_id}")
            return ExtractionResult(overall_confidence=0.0)

        extraction = await self._call_extraction_llm(
            text, CANDIDATE_EXTRACTION_PROMPT
        )
        parsed = self._parse_candidate_extraction(extraction)
        embedding = await self._generate_embedding(text)

        await self._update_candidate(
            supabase, candidate_id, parsed, embedding
        )
        await self._emit_extraction_signal(
            supabase,
            candidate_id,
            candidate.get("created_by"),
            parsed.overall_confidence,
        )

        return parsed

    async def extract_role(self, role_id: UUID) -> RoleExtractionResult:
        """Run AI extraction on a role description."""
        supabase = get_supabase_admin()

        result = (
            supabase.table("roles")
            .select("*")
            .eq("id", str(role_id))
            .single()
            .execute()
        )
        role = result.data

        if not role:
            raise ValueError(f"Role {role_id} not found")

        text = f"{role.get('title', '')}\n\n{role.get('description', '')}"

        extraction = await self._call_extraction_llm(
            text, ROLE_EXTRACTION_PROMPT
        )
        parsed = self._parse_role_extraction(extraction)
        embedding = await self._generate_embedding(text)

        update_data = {
            "required_skills": parsed.required_skills,
            "preferred_skills": parsed.preferred_skills,
            "seniority": (
                parsed.seniority.value if parsed.seniority else None
            ),
            "salary_band": (
                parsed.salary_band.model_dump(mode="json")
                if parsed.salary_band
                else None
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
        """Call GPT-4o for structured extraction with retry."""
        for attempt in range(2):
            try:
                response = await openai_client.chat.completions.create(
                    model=settings.openai_model,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text},
                    ],
                    temperature=0.1,
                    max_tokens=2000,
                )

                content = response.choices[0].message.content
                return json.loads(content)

            except json.JSONDecodeError as e:
                logger.warning(
                    f"LLM returned invalid JSON (attempt {attempt + 1}): {e}"
                )
                if attempt == 1:
                    return {}
            except Exception as e:
                logger.error(
                    f"LLM extraction failed (attempt {attempt + 1}): {e}"
                )
                if attempt == 1:
                    return {}

        return {}

    async def _generate_embedding(self, text: str) -> list[float] | None:
        """Generate embedding via text-embedding-3-small."""
        if not text:
            return None

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

        if not parts:
            name = f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}".strip()
            if name:
                parts.append(f"Name: {name}")

            skills = candidate.get("skills", [])
            if skills:
                skill_names = [
                    s.get("name", "") for s in skills if s.get("name")
                ]
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

        skills = []
        for s in raw.get("skills", []):
            skills.append(
                ExtractedSkill(
                    name=s.get("name", ""),
                    years=s.get("years"),
                    confidence=s.get("confidence", 0.5),
                )
            )

        experience = []
        for e in raw.get("experience", []):
            experience.append(
                ExperienceEntry(
                    company=e.get("company", ""),
                    title=e.get("title", ""),
                    duration_months=e.get("duration_months"),
                    industry=e.get("industry"),
                )
            )

        seniority = None
        seniority_str = raw.get("seniority")
        if seniority_str:
            try:
                seniority = SeniorityLevel(seniority_str)
            except ValueError:
                logger.warning(f"Invalid seniority: {seniority_str}")

        salary = None
        salary_raw = raw.get("salary_expectation")
        if salary_raw and (
            salary_raw.get("min_amount") or salary_raw.get("max_amount")
        ):
            salary = SalaryRange(
                min_amount=(
                    Decimal(str(salary_raw["min_amount"]))
                    if salary_raw.get("min_amount")
                    else None
                ),
                max_amount=(
                    Decimal(str(salary_raw["max_amount"]))
                    if salary_raw.get("max_amount")
                    else None
                ),
                currency=salary_raw.get("currency", "GBP"),
            )

        availability = None
        avail_str = raw.get("availability")
        if avail_str:
            try:
                availability = AvailabilityStatus(avail_str)
            except ValueError:
                logger.warning(f"Invalid availability: {avail_str}")

        industries = raw.get("industries", [])

        all_confidences = []
        for field_name, conf in field_confidences.items():
            all_confidences.append(conf)
            if conf < self.CONFIDENCE_THRESHOLD:
                flagged_fields.append(field_name)

        overall_confidence = (
            sum(all_confidences) / len(all_confidences)
            if all_confidences
            else 0.0
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

        seniority = None
        seniority_str = raw.get("seniority")
        if seniority_str:
            try:
                seniority = SeniorityLevel(seniority_str)
            except ValueError:
                pass

        salary_band = None
        salary_raw = raw.get("salary_band")
        if salary_raw and (
            salary_raw.get("min_amount") or salary_raw.get("max_amount")
        ):
            salary_band = SalaryRange(
                min_amount=(
                    Decimal(str(salary_raw["min_amount"]))
                    if salary_raw.get("min_amount")
                    else None
                ),
                max_amount=(
                    Decimal(str(salary_raw["max_amount"]))
                    if salary_raw.get("max_amount")
                    else None
                ),
                currency=salary_raw.get("currency", "GBP"),
            )

        all_confidences = list(field_confidences.values())
        overall_confidence = (
            sum(all_confidences) / len(all_confidences)
            if all_confidences
            else 0.0
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
            "seniority": (
                extraction.seniority.value if extraction.seniority else None
            ),
            "salary_expectation": (
                extraction.salary_expectation.model_dump(mode="json")
                if extraction.salary_expectation
                else None
            ),
            "availability": (
                extraction.availability.value
                if extraction.availability
                else None
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
