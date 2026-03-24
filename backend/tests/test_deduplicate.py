from pipelines.deduplicate import (
    DeduplicationPipeline,
    _merge_experience,
    _merge_skills,
    _pick_best_field,
)


class TestPickBestField:
    def test_existing_preferred(self):
        assert _pick_best_field("existing", "incoming") == "existing"

    def test_incoming_when_existing_null(self):
        assert _pick_best_field(None, "incoming") == "incoming"

    def test_existing_when_incoming_null(self):
        assert _pick_best_field("existing", None) == "existing"

    def test_both_null(self):
        assert _pick_best_field(None, None) is None

    def test_empty_string_treated_as_null(self):
        assert _pick_best_field("", "incoming") == "incoming"


class TestMergeSkills:
    def test_no_overlap(self):
        existing = [{"name": "Python", "confidence": 0.9}]
        incoming = [{"name": "Java", "confidence": 0.8}]
        result = _merge_skills(existing, incoming)
        assert len(result) == 2

    def test_overlapping_keeps_higher_confidence(self):
        existing = [{"name": "Python", "confidence": 0.7}]
        incoming = [{"name": "Python", "confidence": 0.9}]
        result = _merge_skills(existing, incoming)
        assert len(result) == 1
        assert result[0]["confidence"] == 0.9

    def test_case_insensitive(self):
        existing = [{"name": "python", "confidence": 0.9}]
        incoming = [{"name": "Python", "confidence": 0.8}]
        result = _merge_skills(existing, incoming)
        assert len(result) == 1

    def test_years_preserved(self):
        existing = [{"name": "Python", "confidence": 0.9, "years": None}]
        incoming = [{"name": "Python", "confidence": 0.7, "years": 5.0}]
        result = _merge_skills(existing, incoming)
        assert result[0].get("years") == 5.0


class TestMergeExperience:
    def test_no_overlap(self):
        existing = [{"company": "Revolut", "title": "Senior Engineer"}]
        incoming = [{"company": "Monzo", "title": "Backend Engineer"}]
        result = _merge_experience(existing, incoming)
        assert len(result) == 2

    def test_dedup_same_position(self):
        existing = [
            {
                "company": "Revolut",
                "title": "Senior Engineer",
                "duration_months": None,
            }
        ]
        incoming = [
            {
                "company": "Revolut",
                "title": "Senior Engineer",
                "duration_months": 24,
            }
        ]
        result = _merge_experience(existing, incoming)
        assert len(result) == 1
        assert result[0]["duration_months"] == 24


class TestMatchConfidence:
    def setup_method(self):
        self.pipeline = DeduplicationPipeline()

    def test_exact_email_match(self):
        candidate = {
            "email": "james@example.com",
            "first_name": "James",
            "last_name": "Hartley",
        }
        existing = {
            "email": "james@example.com",
            "first_name": "J",
            "last_name": "H",
        }
        confidence, strategies, _ = self.pipeline._compute_match_confidence(
            candidate, existing
        )
        assert confidence >= 0.9
        assert "exact_email" in strategies

    def test_exact_phone_match(self):
        candidate = {
            "phone": "+44 7700 100001",
            "first_name": "James",
            "last_name": "Hartley",
        }
        existing = {
            "phone": "+447700100001",
            "first_name": "J",
            "last_name": "H",
        }
        confidence, strategies, _ = self.pipeline._compute_match_confidence(
            candidate, existing
        )
        assert confidence >= 0.9
        assert "exact_phone" in strategies

    def test_fuzzy_name_employer_match(self):
        candidate = {
            "first_name": "James",
            "last_name": "Hartley",
            "experience": [{"company": "Revolut"}],
        }
        existing = {
            "first_name": "James",
            "last_name": "Hartley",
            "experience": [{"company": "Revolut"}],
        }
        confidence, strategies, _ = self.pipeline._compute_match_confidence(
            candidate, existing
        )
        assert confidence >= 0.6
        assert "fuzzy_name_employer" in strategies

    def test_no_match(self):
        candidate = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        existing = {
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "bob@example.com",
        }
        confidence, strategies, _ = self.pipeline._compute_match_confidence(
            candidate, existing
        )
        assert confidence < 0.6

    def test_multiple_strategies_boost(self):
        candidate = {
            "email": "james@example.com",
            "first_name": "James",
            "last_name": "Hartley",
            "experience": [{"company": "Revolut"}],
        }
        existing = {
            "email": "james@example.com",
            "first_name": "James",
            "last_name": "Hartley",
            "experience": [{"company": "Revolut"}],
        }
        confidence, strategies, _ = self.pipeline._compute_match_confidence(
            candidate, existing
        )
        assert len(strategies) >= 2
        assert confidence > 0.9
