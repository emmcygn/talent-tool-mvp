"""
Integration tests that verify end-to-end flows across all endpoints.
Run with: python -m pytest tests/test_integration.py -v

Note: These tests use TestClient without real Supabase/auth.
Endpoints that require auth will return 401/403 — that is also correct behaviour.
"""

import pytest
from uuid import uuid4

from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth_headers():
    """Mock auth headers for testing (will result in 401 — correct behaviour)."""
    return {"Authorization": "Bearer test-token"}


class TestHealthAndBootstrap:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_has_version(self, client):
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert "service" in data


class TestOpenAPISchema:
    def test_openapi_schema_available(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema

    def test_api_paths_registered(self, client):
        response = client.get("/openapi.json")
        paths = response.json()["paths"]
        # Verify all major route groups are registered
        assert any("/api/candidates" in p for p in paths)
        assert any("/api/roles" in p for p in paths)
        assert any("/api/matches" in p for p in paths)
        assert any("/api/collections" in p for p in paths)
        assert any("/api/handoffs" in p for p in paths)
        assert any("/api/quotes" in p for p in paths)
        assert any("/api/copilot" in p for p in paths)
        assert any("/api/signals" in p for p in paths)
        assert any("/api/admin" in p for p in paths)


class TestCandidateFlow:
    def test_list_candidates_requires_auth(self, client, auth_headers):
        response = client.get("/api/candidates", headers=auth_headers)
        # With a fake token, expect 401
        assert response.status_code == 401

    def test_list_candidates_no_auth(self, client):
        response = client.get("/api/candidates")
        assert response.status_code in (401, 403)


class TestRoleFlow:
    def test_list_roles_requires_auth(self, client, auth_headers):
        response = client.get("/api/roles", headers=auth_headers)
        assert response.status_code == 401

    def test_list_roles_no_auth(self, client):
        response = client.get("/api/roles")
        assert response.status_code in (401, 403)


class TestHandoffFlow:
    def test_inbox_requires_auth(self, client, auth_headers):
        response = client.get("/api/handoffs/inbox", headers=auth_headers)
        assert response.status_code == 401

    def test_outbox_requires_auth(self, client, auth_headers):
        response = client.get("/api/handoffs/outbox", headers=auth_headers)
        assert response.status_code == 401

    def test_handoff_no_auth(self, client):
        response = client.get(f"/api/handoffs/{uuid4()}")
        assert response.status_code in (401, 403)


class TestQuoteFlow:
    def test_list_quotes_requires_auth(self, client, auth_headers):
        response = client.get("/api/quotes/", headers=auth_headers)
        assert response.status_code == 401

    def test_generate_quote_requires_auth(self, client, auth_headers):
        response = client.post("/api/quotes/generate", json={
            "candidate_id": str(uuid4()),
            "role_id": str(uuid4()),
        }, headers=auth_headers)
        assert response.status_code == 401


class TestCopilotFlow:
    def test_copilot_query_requires_auth(self, client, auth_headers):
        response = client.post("/api/copilot/query", json={
            "query": "Find Python developers in London",
        }, headers=auth_headers)
        assert response.status_code == 401

    def test_copilot_no_auth(self, client):
        response = client.post("/api/copilot/query", json={
            "query": "Find Python developers",
        })
        assert response.status_code in (401, 403)


class TestAdminFlow:
    def test_platform_stats_requires_auth(self, client, auth_headers):
        response = client.get("/api/admin/stats", headers=auth_headers)
        # 401 (invalid token) or 403 (wrong role) — both acceptable
        assert response.status_code in (401, 403)

    def test_adapter_health_requires_auth(self, client, auth_headers):
        response = client.get("/api/admin/adapters/health", headers=auth_headers)
        assert response.status_code in (401, 403)

    def test_admin_no_auth(self, client):
        response = client.get("/api/admin/stats")
        assert response.status_code in (401, 403)


class TestSignalFlow:
    def test_recent_signals_requires_auth(self, client, auth_headers):
        response = client.get("/api/signals/recent", headers=auth_headers)
        assert response.status_code == 401

    def test_funnel_analytics_requires_auth(self, client, auth_headers):
        response = client.get("/api/signals/analytics/funnel", headers=auth_headers)
        assert response.status_code == 401


class TestNotFound:
    def test_unknown_path_returns_404(self, client):
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
