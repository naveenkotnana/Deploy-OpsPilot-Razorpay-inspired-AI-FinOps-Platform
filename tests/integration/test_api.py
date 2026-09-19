"""API integration tests including auth, RBAC and the approval path."""
import pytest
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)


def token(username, password):
    r = client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth(t):
    return {"Authorization": f"Bearer {t}"}


def test_health_is_public():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "up"


def test_root_serves_frontend_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert "OpsPilot" in r.text


def test_favicon_serves_icon():
    r = client.get("/favicon.ico")
    assert r.status_code == 200
    assert "image" in r.headers.get("content-type", "")



def test_login_success_returns_role():
    r = client.post("/auth/login", json={"username": "manager", "password": "manager123"})
    assert r.status_code == 200 and r.json()["role"] == "MANAGER"


def test_login_bad_password_rejected():
    r = client.post("/auth/login", json={"username": "manager", "password": "nope"})
    assert r.status_code == 401


def test_protected_endpoint_requires_credentials():
    assert client.get("/alerts").status_code == 401


def test_invalid_token_rejected():
    assert client.get("/alerts", headers=auth("bogus.token.here")).status_code == 401


def test_alerts_listed_for_analyst():
    r = client.get("/alerts", headers=auth(token("analyst", "analyst123")))
    assert r.status_code == 200 and isinstance(r.json(), list)


def test_revenue_endpoint_returns_rows():
    r = client.get("/revenue", headers=auth(token("analyst", "analyst123")))
    assert r.status_code == 200 and r.json()["row_count"] > 0


def test_revenue_rejects_non_allowlisted_query():
    r = client.get("/revenue?query=evil", headers=auth(token("analyst", "analyst123")))
    assert r.status_code == 400


def test_analyst_cannot_create_incident():
    r = client.post("/incidents", headers=auth(token("analyst", "analyst123")),
                    json={"workflow_id": "WF-X", "title": "t"})
    assert r.status_code == 403


def test_manager_can_create_incident():
    r = client.post("/incidents", headers=auth(token("manager", "manager123")),
                    json={"workflow_id": "WF-RBAC-TEST", "title": "rbac test"})
    assert r.status_code == 200 and r.json()["status"] in ("EXECUTED", "DUPLICATE_SKIPPED")


def test_investigate_creates_workflow():
    t = token("analyst", "analyst123")
    alerts = client.get("/alerts", headers=auth(t)).json()
    if not alerts:
        pytest.skip("no alerts seeded")
    r = client.post(f"/alerts/{alerts[0]['alert_id']}/investigate", headers=auth(t))
    assert r.status_code == 200
    body = r.json()
    assert body["workflow_id"].startswith("WF-")
    assert body["evidence_verdict"] in ("EVIDENCE_SUFFICIENT", "INSUFFICIENT_EVIDENCE")


def test_investigate_unknown_alert_404():
    t = token("analyst", "analyst123")
    assert client.post("/alerts/NOPE/investigate", headers=auth(t)).status_code == 404


def test_analyst_cannot_approve():
    t = token("analyst", "analyst123")
    r = client.post("/workflows/WF-ANY/approve", headers=auth(t), json={"reason": "x"})
    assert r.status_code == 403   # permission denied BEFORE any 404 lookup


def test_metrics_shape():
    r = client.get("/metrics", headers=auth(token("admin", "admin123")))
    assert r.status_code == 200
    j = r.json()
    assert {"api", "workflows", "approvals", "ollama"} <= set(j)


def test_audit_endpoint():
    r = client.get("/audit", headers=auth(token("admin", "admin123")))
    assert r.status_code == 200 and isinstance(r.json(), list)


def test_openapi_generated():
    r = client.get("/openapi.json")
    assert r.status_code == 200 and "paths" in r.json()
