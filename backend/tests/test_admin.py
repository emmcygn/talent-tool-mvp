import pytest
from uuid import uuid4

from api.admin import UserCreate, UserUpdate, _merge_experience, _merge_skills
from contracts.shared import UserRole


def test_merge_skills_dedup():
    skills_a = [
        {"name": "Python", "years": 3, "confidence": 0.9},
        {"name": "FastAPI", "years": 2, "confidence": 0.8},
    ]
    skills_b = [
        {"name": "python", "years": 5, "confidence": 0.95},  # duplicate, higher years
        {"name": "React", "years": 4, "confidence": 0.85},
    ]
    merged = _merge_skills(skills_a, skills_b)
    assert len(merged) == 3  # Python, FastAPI, React

    # Python should have 5 years (higher value)
    python_skill = next(s for s in merged if s["name"].lower() == "python")
    assert python_skill["years"] == 5


def test_merge_skills_empty():
    assert _merge_skills([], []) == []
    assert len(_merge_skills([{"name": "Python", "years": 3}], [])) == 1


def test_merge_skills_keeps_lower_if_existing_higher():
    """When existing skill has more years, keep existing."""
    skills_a = [{"name": "Python", "years": 8}]
    skills_b = [{"name": "Python", "years": 3}]
    merged = _merge_skills(skills_a, skills_b)
    assert len(merged) == 1
    assert merged[0]["years"] == 8


def test_merge_experience_dedup():
    exp_a = [
        {"company": "Acme Corp", "title": "Backend Developer", "duration_months": 24},
    ]
    exp_b = [
        {"company": "Acme Corp", "title": "Backend Developer", "duration_months": 24},  # duplicate
        {"company": "BigCo", "title": "Senior Engineer", "duration_months": 36},
    ]
    merged = _merge_experience(exp_a, exp_b)
    assert len(merged) == 2  # Acme Corp + BigCo


def test_merge_experience_empty():
    assert _merge_experience([], []) == []
    assert len(_merge_experience([{"company": "Acme", "title": "Dev"}], [])) == 1


def test_merge_experience_case_insensitive():
    """Company+title dedup should be case-insensitive."""
    exp_a = [{"company": "Acme Corp", "title": "Developer"}]
    exp_b = [{"company": "acme corp", "title": "developer"}]  # same, different case
    merged = _merge_experience(exp_a, exp_b)
    assert len(merged) == 1


def test_user_create_model():
    u = UserCreate(
        email="admin@test.com",
        first_name="Admin",
        last_name="User",
        role=UserRole.admin,
    )
    assert u.role == UserRole.admin
    assert u.organisation_id is None


def test_user_create_with_org():
    org_id = uuid4()
    u = UserCreate(
        email="partner@test.com",
        first_name="Jane",
        last_name="Smith",
        role=UserRole.talent_partner,
        organisation_id=org_id,
    )
    assert u.organisation_id == org_id


def test_user_update_partial():
    u = UserUpdate(first_name="Updated")
    assert u.first_name == "Updated"
    assert u.last_name is None
    assert u.role is None
    assert u.is_active is None


def test_user_roles():
    """All three user roles must exist."""
    assert UserRole.talent_partner.value == "talent_partner"
    assert UserRole.client.value == "client"
    assert UserRole.admin.value == "admin"
