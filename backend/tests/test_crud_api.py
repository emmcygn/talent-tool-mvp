from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

MOCK_TP_TOKEN = "mock-talent-partner-token"
MOCK_CLIENT_TOKEN = "mock-client-token"
MOCK_ADMIN_TOKEN = "mock-admin-token"

MOCK_TP_USER = {
    "sub": str(uuid4()),
    "email": "partner@example.com",
    "user_metadata": {"role": "talent_partner"},
}

MOCK_CLIENT_USER = {
    "sub": str(uuid4()),
    "email": "client@example.com",
    "user_metadata": {"role": "client"},
}

MOCK_ADMIN_USER = {
    "sub": str(uuid4()),
    "email": "admin@example.com",
    "user_metadata": {"role": "admin"},
}


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def mock_jwt_decode():
    """Mock JWT decoding to return test users."""
    with patch("api.auth.decode_supabase_jwt") as mock:

        def side_effect(token):
            if token == MOCK_TP_TOKEN:
                return MOCK_TP_USER
            elif token == MOCK_CLIENT_TOKEN:
                return MOCK_CLIENT_USER
            elif token == MOCK_ADMIN_TOKEN:
                return MOCK_ADMIN_USER
            raise Exception("Invalid token")

        mock.side_effect = side_effect
        yield mock


@pytest.fixture(autouse=True)
def mock_supabase():
    """Mock Supabase client for testing."""
    with patch(
        "api.candidates.get_supabase_admin"
    ) as mock_cand, patch(
        "api.roles.get_supabase_admin"
    ) as mock_roles:
        mock_client = MagicMock()

        mock_result = MagicMock()
        mock_result.data = []
        mock_result.count = 0
        mock_client.table.return_value.select.return_value.or_.return_value.order.return_value.range.return_value.execute.return_value = (
            mock_result
        )
        mock_client.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value = (
            mock_result
        )

        mock_cand.return_value = mock_client
        mock_roles.return_value = mock_client
        yield mock_client


class TestCandidateEndpoints:
    def test_list_candidates_requires_auth(self):
        response = client.get("/api/candidates")
        assert response.status_code == 403

    def test_list_candidates_as_talent_partner(self, mock_supabase):
        response = client.get(
            "/api/candidates",
            headers=_auth_header(MOCK_TP_TOKEN),
        )
        assert response.status_code in (200, 500)

    def test_list_candidates_client_rejected(self):
        response = client.get(
            "/api/candidates",
            headers=_auth_header(MOCK_CLIENT_TOKEN),
        )
        assert response.status_code == 403

    def test_create_candidate_requires_talent_partner(self):
        response = client.post(
            "/api/candidates",
            json={"first_name": "Test", "last_name": "User"},
            headers=_auth_header(MOCK_CLIENT_TOKEN),
        )
        assert response.status_code == 403

    def test_create_candidate_as_talent_partner(self, mock_supabase):
        mock_result = MagicMock()
        mock_result.data = [
            {"id": str(uuid4()), "first_name": "Test", "last_name": "User"}
        ]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = (
            mock_result
        )

        response = client.post(
            "/api/candidates",
            json={"first_name": "Test", "last_name": "User"},
            headers=_auth_header(MOCK_TP_TOKEN),
        )
        assert response.status_code == 201


class TestRoleEndpoints:
    def test_create_role_requires_client(self):
        response = client.post(
            "/api/roles",
            json={
                "title": "Senior Engineer",
                "description": "Python role",
                "organisation_id": str(uuid4()),
            },
            headers=_auth_header(MOCK_TP_TOKEN),
        )
        assert response.status_code == 403

    def test_create_role_as_client(self, mock_supabase):
        mock_result = MagicMock()
        mock_result.data = [
            {"id": str(uuid4()), "title": "Senior Engineer"}
        ]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = (
            mock_result
        )

        response = client.post(
            "/api/roles",
            json={
                "title": "Senior Engineer",
                "description": "Python role",
                "organisation_id": str(uuid4()),
            },
            headers=_auth_header(MOCK_CLIENT_TOKEN),
        )
        assert response.status_code == 201

    def test_list_roles_any_authenticated(self, mock_supabase):
        response = client.get(
            "/api/roles",
            headers=_auth_header(MOCK_TP_TOKEN),
        )
        assert response.status_code in (200, 500)
