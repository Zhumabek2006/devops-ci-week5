"""Unit tests for the week 3 Flask app, run by the CI test job."""

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_returns_greeting(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json()["message"] == "Hello from DevOps week 3!"


def test_index_reports_hostname(client):
    data = client.get("/").get_json()

    assert isinstance(data["hostname"], str)
    assert data["hostname"] != ""


def test_healthz_is_ok(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_healthz_uptime_is_a_non_negative_number(client):
    uptime = client.get("/healthz").get_json()["uptime_seconds"]

    assert isinstance(uptime, (int, float))
    assert uptime >= 0


def test_unknown_route_returns_404(client):
    assert client.get("/does-not-exist").status_code == 404


def test_healthz_rejects_post(client):
    # /healthz is registered for GET only.
    assert client.post("/healthz").status_code == 405
