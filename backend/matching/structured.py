from uuid import UUID

from contracts.shared import AvailabilityStatus, SalaryRange, SeniorityLevel

SENIORITY_ORDER = {
    SeniorityLevel.junior: 1,
    SeniorityLevel.mid: 2,
    SeniorityLevel.senior: 3,
    SeniorityLevel.lead: 4,
    SeniorityLevel.principal: 5,
}


class StructuredFilter:
    """Filters candidates by hard requirements: location, salary, availability, min experience."""

    def __init__(self, supabase):
        self.supabase = supabase

    async def filter_candidates(
        self,
        role_location: str | None,
        role_salary_band: SalaryRange | None,
        role_seniority: SeniorityLevel | None,
        required_availability: list[AvailabilityStatus] | None = None,
        min_experience_years: float | None = None,
        exclude_candidate_ids: list[UUID] | None = None,
    ) -> list[UUID]:
        """Returns candidate IDs that pass all hard-requirement filters."""
        query = self.supabase.table("candidates").select(
            "id, location, salary_expectation, seniority, availability, skills, experience"
        )
        result = query.execute()
        candidates = result.data

        filtered = []
        for c in candidates:
            cid = c["id"]

            if exclude_candidate_ids and cid in [
                str(eid) for eid in exclude_candidate_ids
            ]:
                continue

            # Location filter
            if role_location and c.get("location"):
                candidate_loc = (c["location"] or "").lower()
                role_loc = role_location.lower()
                if (
                    role_loc not in candidate_loc
                    and "remote" not in candidate_loc
                    and "remote" not in role_loc
                ):
                    continue

            # Salary filter
            if role_salary_band and c.get("salary_expectation"):
                csal = c["salary_expectation"]
                if isinstance(csal, dict):
                    c_min = float(csal.get("min_amount") or 0)
                    c_max = float(csal.get("max_amount") or 999999)
                    r_min = float(role_salary_band.min_amount or 0)
                    r_max = float(role_salary_band.max_amount or 999999)
                    if c_max < r_min or c_min > r_max:
                        continue

            # Availability filter
            if required_availability and c.get("availability"):
                if c["availability"] not in [
                    a.value for a in required_availability
                ]:
                    continue

            # Seniority filter
            if role_seniority and c.get("seniority"):
                candidate_level = SENIORITY_ORDER.get(
                    SeniorityLevel(c["seniority"]), 0
                )
                required_level = SENIORITY_ORDER.get(role_seniority, 0)
                if candidate_level < required_level - 1:
                    continue

            # Min experience years filter
            if min_experience_years is not None:
                total_months = 0
                for exp in c.get("experience") or []:
                    if isinstance(exp, dict):
                        total_months += exp.get("duration_months", 0) or 0
                total_years = total_months / 12.0
                if total_years < min_experience_years:
                    continue

            filtered.append(UUID(cid))

        return filtered
