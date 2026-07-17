# tests/test_server.py

from fastapi.testclient import TestClient
from projectreadmegen.server import app

client = TestClient(app)

def test_get_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "api_key_configured" in data

def test_api_scan():
    response = client.post("/api/scan", json={"path": ".", "use_cache": False})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "scan_result" in data
    assert "detection" in data
    assert data["scan_result"]["name"] != ""

def test_serve_frontend():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "README Gen" in response.text
    assert "Studio v6.0.0" in response.text

def test_api_scan_absolute_path():
    from pathlib import Path
    abs_path = str(Path.cwd().resolve())
    response = client.post("/api/scan", json={"path": abs_path, "use_cache": False})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "resolved_path" in data

