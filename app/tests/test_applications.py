"""
Minimal smoke tests. These run in CI against a throwaway SQLite DB
(see conftest.py) so the pipeline doesn't need a real Postgres instance
just to validate the app boots and the routes behave correctly.
"""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_application(client: TestClient):
    payload = {
        "company": "Acme Corp",
        "role": "DevOps Intern",
        "status": "applied",
        "date_applied": "2026-07-01",
        "notes": "Referred by a friend",
    }
    create_resp = client.post("/applications", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["company"] == "Acme Corp"

    get_resp = client.get(f"/applications/{created['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["role"] == "DevOps Intern"


def test_update_status(client: TestClient):
    payload = {
        "company": "Globex",
        "role": "Cloud Engineer Intern",
        "date_applied": "2026-07-05",
    }
    created = client.post("/applications", json=payload).json()

    patch_resp = client.patch(f"/applications/{created['id']}", json={"status": "interviewing"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "interviewing"


def test_get_nonexistent_application_returns_404(client: TestClient):
    response = client.get("/applications/999999")
    assert response.status_code == 404


def test_delete_application(client: TestClient):
    payload = {
        "company": "Initech",
        "role": "Platform Intern",
        "date_applied": "2026-07-10",
    }
    created = client.post("/applications", json=payload).json()

    delete_resp = client.delete(f"/applications/{created['id']}")
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/applications/{created['id']}")
    assert get_resp.status_code == 404
