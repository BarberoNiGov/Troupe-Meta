from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        data = client.get("/health").json()
        assert data["status"] == "ok"
        assert data["provider"]


def test_config_has_full_roster_and_default_cast():
    with TestClient(app) as client:
        data = client.get("/config").json()
        assert len(data["personas"]) == 11
        assert len(data["default_cast"]) == 8
        assert len(data["flavor_pack"]) == 3
        assert data["max_cast"] == 8
        assert data["three_d_default"] is False
        assert data["modes"] == ["2d", "3d", "hybrid"]
        assert data["mode_default"] == "2d"
        assert data["brief"]
        assert "experiment" in data


def test_run_rejects_empty_brief():
    with TestClient(app) as client:
        response = client.post("/run", json={"brief": "   "})
        assert response.status_code == 400


def test_run_rejects_too_many_agents():
    with TestClient(app) as client:
        ids = [p["id"] for p in client.get("/config").json()["personas"]][:9]
        response = client.post("/run", json={"brief": "test", "persona_ids": ids})
        assert response.status_code == 400


def test_run_rejects_unknown_agent():
    with TestClient(app) as client:
        response = client.post("/run", json={"brief": "test", "persona_ids": ["baseline", "nope", "stoic"]})
        assert response.status_code == 400


def test_run_rejects_non_boolean_three_d():
    with TestClient(app) as client:
        response = client.post("/run", json={"brief": "test", "three_d": "yes"})
        assert response.status_code == 400


def test_run_rejects_unknown_mode():
    with TestClient(app) as client:
        response = client.post("/run", json={"brief": "test", "mode": "4d"})
        assert response.status_code == 400
