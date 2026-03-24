import logging
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel

from adapters.base import AdapterCandidate
from adapters.registry import adapter_registry
from api.deps import get_supabase_admin
from contracts.shared import SignalType, UserRole
from pipelines.normalize import NormalizedCandidate, normalize_candidate

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
        """Ingest candidates from a single adapter."""
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
                error_msg = (
                    f"Normalization failed for {record.external_id}: {e}"
                )
                logger.warning(error_msg)
                errors.append(error_msg)

        logger.info(
            f"Normalized {len(normalized)}/{len(raw_records)} records"
        )

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
        """Store a normalized candidate in the candidates table."""
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
            "seniority": (
                candidate.seniority.value if candidate.seniority else None
            ),
            "salary_expectation": (
                candidate.salary_expectation.model_dump(mode="json")
                if candidate.salary_expectation
                else None
            ),
            "availability": (
                candidate.availability.value if candidate.availability else None
            ),
            "industries": candidate.industries,
            "sources": [candidate.source.model_dump()],
            "extraction_confidence": None,
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
            "entity_id": str(uuid4()),
            "metadata": {
                "adapter_name": adapter_name,
                "candidate_email": candidate_email,
            },
        }
        try:
            supabase.table("signals").insert(signal).execute()
        except Exception as e:
            logger.warning(f"Failed to emit ingestion signal: {e}")
