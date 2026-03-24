from contracts.shared import (
    ConfidenceLevel,
    ExtractedSkill,
    RequiredSkill,
    SeniorityLevel,
    SkillMatch,
)

# Scoring weights
WEIGHT_SKILL_OVERLAP = 0.40
WEIGHT_SEMANTIC_SIMILARITY = 0.35
WEIGHT_EXPERIENCE_FIT = 0.25

SENIORITY_ORDER = {
    SeniorityLevel.junior: 1,
    SeniorityLevel.mid: 2,
    SeniorityLevel.senior: 3,
    SeniorityLevel.lead: 4,
    SeniorityLevel.principal: 5,
}


class CompositeScorer:
    """Scores candidates against roles using weighted combination of three factors."""

    def score(
        self,
        candidate_skills: list[ExtractedSkill],
        candidate_seniority: SeniorityLevel | None,
        candidate_experience_months: int,
        role_required_skills: list[RequiredSkill],
        role_preferred_skills: list[RequiredSkill],
        role_seniority: SeniorityLevel | None,
        semantic_similarity: float,
    ) -> dict:
        """Compute composite score and return full breakdown."""
        # 1. Skill overlap scoring
        skill_overlap, skill_score = self._compute_skill_overlap(
            candidate_skills, role_required_skills, role_preferred_skills
        )

        # 2. Semantic similarity (already 0-1 from pgvector)
        semantic_score = max(0.0, min(1.0, semantic_similarity))

        # 3. Experience / seniority fit
        experience_score = self._compute_experience_fit(
            candidate_seniority, role_seniority, candidate_experience_months
        )

        # 4. Composite
        overall = (
            WEIGHT_SKILL_OVERLAP * skill_score
            + WEIGHT_SEMANTIC_SIMILARITY * semantic_score
            + WEIGHT_EXPERIENCE_FIT * experience_score
        )
        overall = round(overall, 4)

        # 5. Confidence bucket
        confidence = self._bucket_confidence(overall)

        return {
            "overall_score": overall,
            "structured_score": round(skill_score, 4),
            "semantic_score": round(semantic_score, 4),
            "experience_score": round(experience_score, 4),
            "skill_overlap": skill_overlap,
            "confidence": confidence,
            "scoring_breakdown": {
                "weights": {
                    "skill_overlap": WEIGHT_SKILL_OVERLAP,
                    "semantic_similarity": WEIGHT_SEMANTIC_SIMILARITY,
                    "experience_fit": WEIGHT_EXPERIENCE_FIT,
                },
                "components": {
                    "skill_overlap_raw": round(skill_score, 4),
                    "semantic_similarity_raw": round(semantic_score, 4),
                    "experience_fit_raw": round(experience_score, 4),
                },
                "weighted_components": {
                    "skill_overlap_weighted": round(
                        WEIGHT_SKILL_OVERLAP * skill_score, 4
                    ),
                    "semantic_similarity_weighted": round(
                        WEIGHT_SEMANTIC_SIMILARITY * semantic_score, 4
                    ),
                    "experience_fit_weighted": round(
                        WEIGHT_EXPERIENCE_FIT * experience_score, 4
                    ),
                },
                "overall_score": overall,
            },
        }

    def _compute_skill_overlap(
        self,
        candidate_skills: list[ExtractedSkill],
        required_skills: list[RequiredSkill],
        preferred_skills: list[RequiredSkill],
    ) -> tuple[list[SkillMatch], float]:
        """Compare candidate skills against required + preferred skills."""
        c_skills = {}
        for s in candidate_skills:
            c_skills[s.name.lower().strip()] = s

        overlaps: list[SkillMatch] = []
        total_weight = 0.0
        earned_weight = 0.0

        for skill in required_skills:
            weight = 2.0
            total_weight += weight
            skill_name_lower = skill.name.lower().strip()

            match = self._find_skill_match(skill_name_lower, c_skills)
            if match:
                if skill.min_years and match.years:
                    if match.years >= skill.min_years:
                        status = "matched"
                        earned_weight += weight
                    else:
                        status = "partial"
                        ratio = match.years / skill.min_years
                        earned_weight += weight * min(ratio, 1.0) * 0.7
                else:
                    status = "matched"
                    earned_weight += weight

                overlaps.append(
                    SkillMatch(
                        skill_name=skill.name,
                        status=status,
                        candidate_years=match.years,
                        required_years=skill.min_years,
                    )
                )
            else:
                overlaps.append(
                    SkillMatch(
                        skill_name=skill.name,
                        status="missing",
                        candidate_years=None,
                        required_years=skill.min_years,
                    )
                )

        for skill in preferred_skills:
            weight = 1.0
            total_weight += weight
            skill_name_lower = skill.name.lower().strip()

            match = self._find_skill_match(skill_name_lower, c_skills)
            if match:
                earned_weight += weight
                overlaps.append(
                    SkillMatch(
                        skill_name=skill.name,
                        status="matched",
                        candidate_years=match.years,
                        required_years=skill.min_years,
                    )
                )
            else:
                overlaps.append(
                    SkillMatch(
                        skill_name=skill.name,
                        status="missing",
                        candidate_years=None,
                        required_years=skill.min_years,
                    )
                )

        score = (earned_weight / total_weight) if total_weight > 0 else 0.5
        return overlaps, min(score, 1.0)

    def _find_skill_match(
        self, target: str, candidate_skills: dict[str, ExtractedSkill]
    ) -> ExtractedSkill | None:
        """Find a matching skill with alias support."""
        if target in candidate_skills:
            return candidate_skills[target]

        ALIASES = {
            "javascript": ["js", "ecmascript"],
            "typescript": ["ts"],
            "python": ["py"],
            "react": ["reactjs", "react.js"],
            "node": ["nodejs", "node.js"],
            "postgresql": ["postgres", "psql"],
            "kubernetes": ["k8s"],
            "amazon web services": ["aws"],
            "google cloud platform": ["gcp"],
            "machine learning": ["ml"],
            "artificial intelligence": ["ai"],
            "ci/cd": ["cicd", "continuous integration"],
            "docker": ["containerization"],
        }

        for canonical, aliases in ALIASES.items():
            all_names = [canonical] + aliases
            if target in all_names:
                for name in all_names:
                    if name in candidate_skills:
                        return candidate_skills[name]

        # Substring matching as fallback
        for skill_name, skill in candidate_skills.items():
            if target in skill_name or skill_name in target:
                return skill

        return None

    def _compute_experience_fit(
        self,
        candidate_seniority: SeniorityLevel | None,
        role_seniority: SeniorityLevel | None,
        candidate_experience_months: int,
    ) -> float:
        """Score experience/seniority fit. Perfect=1.0, one level off=0.7."""
        if not role_seniority:
            return 0.7

        if not candidate_seniority:
            years = candidate_experience_months / 12.0
            if years >= 10:
                candidate_seniority = SeniorityLevel.principal
            elif years >= 7:
                candidate_seniority = SeniorityLevel.lead
            elif years >= 4:
                candidate_seniority = SeniorityLevel.senior
            elif years >= 2:
                candidate_seniority = SeniorityLevel.mid
            else:
                candidate_seniority = SeniorityLevel.junior

        c_level = SENIORITY_ORDER.get(candidate_seniority, 2)
        r_level = SENIORITY_ORDER.get(role_seniority, 2)
        diff = abs(c_level - r_level)

        if diff == 0:
            return 1.0
        elif diff == 1:
            return 0.7
        elif diff == 2:
            return 0.3
        else:
            return 0.1

    def _bucket_confidence(self, overall_score: float) -> ConfidenceLevel:
        """Bucket overall score into confidence levels."""
        if overall_score > 0.75:
            return ConfidenceLevel.strong
        elif overall_score >= 0.5:
            return ConfidenceLevel.good
        else:
            return ConfidenceLevel.possible
