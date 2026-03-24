from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_check():
    """Health endpoint returns 200 with correct payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "recruittech-api"
    assert "version" in data


def test_health_check_has_request_id():
    """Logging middleware adds X-Request-ID header."""
    response = client.get("/health")
    assert "x-request-id" in response.headers


def test_not_found():
    """Non-existent routes return structured 404."""
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
