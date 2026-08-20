import pytest

from main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "genai-poc-app"


def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "GenAI" in resp.get_json()["message"]
