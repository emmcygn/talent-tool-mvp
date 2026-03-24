import json
import logging
from uuid import UUID

from openai import AsyncOpenAI

from config import settings
from contracts.shared import ConfidenceLevel

logger = logging.getLogger("recruittech.matching.explainer")

CONFIDENCE_LABELS = {
    ConfidenceLevel.strong: "Strong Match",
    ConfidenceLevel.good: "Good Match",
    ConfidenceLevel.possible: "Worth Considering",
}

EXPLANATION_SYSTEM_PROMPT = """You are an expert recruitment consultant writing match explanations for a UK-based recruitment platform. Your audience is non-technical recruitment partners and hiring managers.

Rules:
- Write in plain English. No jargon, no raw scores, no technical metrics.
- Be specific about the candidate's relevant experience and how it aligns with the role.
- Mention specific skills, years of experience, and industry context where relevant.
- Be honest about gaps — if skills are missing, say so constructively.
- Keep the tone professional but warm. Think "trusted advisor", not "algorithm output".
- Use UK English spelling (e.g., "organisation", "specialised").
- Never fabricate experience or skills — only reference what is provided in the data.
- Strengths and gaps should be concise bullet points (one line each).
- The recommendation should be a single actionable sentence.

You will receive structured data about a candidate and role match. Return your response as JSON."""

EXPLANATION_USER_PROMPT_TEMPLATE = """Generate a match explanation for this candidate-role pairing.

## Role
- Title: {role_title}
- Required Skills: {required_skills}
- Preferred Skills: {preferred_skills}
- Seniority: {role_seniority}
- Location: {role_location}
- Industry: {role_industry}

## Candidate
- Current/Recent Title: {candidate_title}
- Seniority: {candidate_seniority}
- Location: {candidate_location}
- Total Experience: {candidate_experience_years} years
- Key Skills: {candidate_skills}
- Industries: {candidate_industries}
- Availability: {candidate_availability}

## Match Data
- Confidence Level: {confidence_label}
- Skills Matched: {skills_matched}
- Skills Partially Matched: {skills_partial}
- Skills Missing: {skills_missing}
- Semantic Similarity: {semantic_description}
- Experience Fit: {experience_description}

Return JSON with this exact structure:
{{
    "explanation": "2-3 sentence plain-English explanation of why this candidate matches (or doesn't match) this role.",
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "gaps": ["gap 1", "gap 2"],
    "recommendation": "One actionable sentence recommending next steps."
}}"""


class MatchExplainer:
    """Generates plain-English match explanations using an LLM."""

    def __init__(self, supabase):
        self.supabase = supabase
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.model_version = f"{settings.openai_model}-explainer-v1"

    async def generate_explanations(
        self,
        role_id: UUID,
        min_confidence: ConfidenceLevel = ConfidenceLevel.good,
    ) -> int:
        """Generate explanations for all matches of a role at or above min_confidence."""
        confidence_values = self._get_confidence_values_at_or_above(
            min_confidence
        )

        matches_result = (
            self.supabase.table("matches")
            .select("*")
            .eq("role_id", str(role_id))
            .in_("confidence", confidence_values)
            .or_("explanation.is.null,explanation.eq.")
            .execute()
        )

        matches = matches_result.data or []
        if not matches:
            return 0

        role_result = (
            self.supabase.table("roles")
            .select("*")
            .eq("id", str(role_id))
            .single()
            .execute()
        )
        role = role_result.data

        candidate_ids = [m["candidate_id"] for m in matches]
        candidates_result = (
            self.supabase.table("candidates")
            .select("*")
            .in_("id", candidate_ids)
            .execute()
        )
        candidates_map = {
            c["id"]: c for c in (candidates_result.data or [])
        }

        count = 0
        for match in matches:
            candidate = candidates_map.get(match["candidate_id"])
            if not candidate:
                continue

            explanation = await self._generate_single(role, candidate, match)
            if explanation:
                self.supabase.table("matches").update(
                    {
                        "explanation": explanation["explanation"],
                        "strengths": explanation["strengths"],
                        "gaps": explanation["gaps"],
                        "recommendation": explanation["recommendation"],
                        "model_version": self.model_version,
                    }
                ).eq("id", match["id"]).execute()
                count += 1

        return count

    async def generate_single_explanation(
        self,
        match_id: UUID,
    ) -> dict | None:
        """Re-generate explanation for a single match."""
        match_result = (
            self.supabase.table("matches")
            .select("*")
            .eq("id", str(match_id))
            .single()
            .execute()
        )
        match = match_result.data
        if not match:
            return None

        role_result = (
            self.supabase.table("roles")
            .select("*")
            .eq("id", match["role_id"])
            .single()
            .execute()
        )
        role = role_result.data

        candidate_result = (
            self.supabase.table("candidates")
            .select("*")
            .eq("id", match["candidate_id"])
            .single()
            .execute()
        )
        candidate = candidate_result.data

        if not role or not candidate:
            return None

        explanation = await self._generate_single(role, candidate, match)
        if explanation:
            self.supabase.table("matches").update(
                {
                    "explanation": explanation["explanation"],
                    "strengths": explanation["strengths"],
                    "gaps": explanation["gaps"],
                    "recommendation": explanation["recommendation"],
                    "model_version": self.model_version,
                }
            ).eq("id", match["id"]).execute()

        return explanation

    async def _generate_single(
        self,
        role: dict,
        candidate: dict,
        match: dict,
    ) -> dict | None:
        """Generate explanation for a single candidate-role match."""
        skill_overlap = match.get("skill_overlap") or []
        skills_matched = [
            s["skill_name"]
            for s in skill_overlap
            if s.get("status") == "matched"
        ]
        skills_partial = [
            s["skill_name"]
            for s in skill_overlap
            if s.get("status") == "partial"
        ]
        skills_missing = [
            s["skill_name"]
            for s in skill_overlap
            if s.get("status") == "missing"
        ]

        semantic_score = match.get("semantic_score", 0)
        if semantic_score > 0.8:
            semantic_description = "Very high profile similarity — candidate's overall experience closely mirrors the role requirements"
        elif semantic_score > 0.6:
            semantic_description = "Good profile similarity — significant overlap in experience and domain"
        elif semantic_score > 0.4:
            semantic_description = "Moderate profile similarity — some relevant overlap"
        else:
            semantic_description = "Lower profile similarity — candidate's background differs from typical candidates for this role"

        experience_score = (
            match.get("scoring_breakdown", {})
            .get("components", {})
            .get("experience_fit_raw", 0.5)
        )
        if experience_score >= 0.9:
            experience_description = "Excellent seniority and experience match"
        elif experience_score >= 0.6:
            experience_description = (
                "Good experience level, close to requirements"
            )
        else:
            experience_description = (
                "Experience level differs from role requirements"
            )

        experience = candidate.get("experience") or []
        candidate_title = (
            experience[0].get("title", "Not specified")
            if experience
            else "Not specified"
        )

        candidate_skills_list = candidate.get("skills") or []
        candidate_skills_str = (
            ", ".join(
                f"{s['name']} ({s.get('years', '?')}y)"
                for s in candidate_skills_list[:10]
            )
            or "None extracted"
        )

        confidence = ConfidenceLevel(match.get("confidence", "possible"))
        confidence_label = CONFIDENCE_LABELS.get(
            confidence, "Worth Considering"
        )

        total_months = sum(
            (e.get("duration_months") or 0)
            for e in experience
            if isinstance(e, dict)
        )

        prompt = EXPLANATION_USER_PROMPT_TEMPLATE.format(
            role_title=role.get("title", ""),
            required_skills=", ".join(
                s.get("name", "")
                for s in (role.get("required_skills") or [])
            )
            or "None specified",
            preferred_skills=", ".join(
                s.get("name", "")
                for s in (role.get("preferred_skills") or [])
            )
            or "None specified",
            role_seniority=role.get("seniority", "Not specified"),
            role_location=role.get("location", "Not specified"),
            role_industry=role.get("industry", "Not specified"),
            candidate_title=candidate_title,
            candidate_seniority=candidate.get("seniority", "Not specified"),
            candidate_location=candidate.get("location", "Not specified"),
            candidate_experience_years=round(total_months / 12, 1),
            candidate_skills=candidate_skills_str,
            candidate_industries=", ".join(
                candidate.get("industries") or []
            )
            or "Not specified",
            candidate_availability=candidate.get(
                "availability", "Not specified"
            ),
            confidence_label=confidence_label,
            skills_matched=", ".join(skills_matched) or "None",
            skills_partial=", ".join(skills_partial) or "None",
            skills_missing=", ".join(skills_missing) or "None",
            semantic_description=semantic_description,
            experience_description=experience_description,
        )

        try:
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": EXPLANATION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=500,
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            return {
                "explanation": result.get("explanation", ""),
                "strengths": result.get("strengths", [])[:5],
                "gaps": result.get("gaps", [])[:5],
                "recommendation": result.get("recommendation", ""),
            }

        except Exception as e:
            logger.warning(f"LLM explanation failed, using fallback: {e}")
            return self._generate_fallback(
                confidence_label,
                skills_matched,
                skills_partial,
                skills_missing,
                candidate,
                role,
            )

    def _generate_fallback(
        self,
        confidence_label: str,
        skills_matched: list[str],
        skills_partial: list[str],
        skills_missing: list[str],
        candidate: dict,
        role: dict,
    ) -> dict:
        """Generate a basic explanation without LLM as fallback."""
        name = candidate.get("first_name", "Candidate")
        role_title = role.get("title", "this role")

        explanation_parts = []
        if skills_matched:
            explanation_parts.append(
                f"{name} brings relevant experience in {', '.join(skills_matched[:3])}."
            )
        if skills_missing:
            explanation_parts.append(
                f"However, experience in {', '.join(skills_missing[:2])} would strengthen the match."
            )

        if not explanation_parts:
            explanation = f"{name} has been identified as a {confidence_label.lower()} for {role_title}."
        else:
            explanation = " ".join(explanation_parts)
            if name not in explanation:
                explanation = f"{name}: {explanation}"

        strengths = [f"Experience with {s}" for s in skills_matched[:3]]
        gaps = [
            f"No demonstrated experience in {s}" for s in skills_missing[:3]
        ]
        recommendation = f"Consider {name} for an introductory conversation to assess cultural fit and specific experience depth."

        return {
            "explanation": explanation,
            "strengths": strengths,
            "gaps": gaps,
            "recommendation": recommendation,
        }

    def _get_confidence_values_at_or_above(
        self, min_confidence: ConfidenceLevel
    ) -> list[str]:
        """Return confidence level values at or above the minimum."""
        order = [
            ConfidenceLevel.possible,
            ConfidenceLevel.good,
            ConfidenceLevel.strong,
        ]
        idx = order.index(min_confidence)
        return [c.value for c in order[idx:]]
