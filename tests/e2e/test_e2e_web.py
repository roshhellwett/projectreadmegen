"""End-to-End Web Studio & REST API Lifecycle Tests for Project README Gen 5.1.13.

Tests full HTTP endpoints, multi-step scanning & template generation pipelines,
GitHub Profile presets, and atomic key synchronization between Web and CLI state.
"""

from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from projectreadmegen import server, usagetracker, grok, github_profile

client = TestClient(server.app)


def test_e2e_web_scan_and_generate_lifecycle(tmp_path: Path, monkeypatch):
    """E2E Test: Full REST API scan -> template generation -> AI synthesis pipeline."""
    # Create sample project structure inside temporary directory
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "index.js").write_text("console.log('Hello Web E2E Studio');\n", encoding="utf-8")
    (tmp_path / "package.json").write_text('{"name": "web-studio-test", "scripts": {"test": "jest"}}\n', encoding="utf-8")
    (tmp_path / "index.html").write_text("<!DOCTYPE html><html><head><title>App</title></head><body><div id='root'></div></body></html>\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "api.md").write_text("# API Docs\n", encoding="utf-8")

    # Monkeypatch workspace root so the path-traversal guard allows tmp_path
    monkeypatch.setattr(server, "_WORKSPACE_ROOT", tmp_path.resolve())

    # Step 1: POST /api/scan — use "." since workspace root is now tmp_path
    scan_res = client.post("/api/scan", json={"path": "."})
    assert scan_res.status_code == 200, f"Scan failed: {scan_res.text}"
    scan_data = scan_res.json()
    assert "scan_result" in scan_data
    assert "detection" in scan_data
    assert scan_data["detection"]["project_type"] == "web-app"
    assert scan_data["detection"]["has_tests"] is True

    # Step 2: POST /api/generate across multiple template options
    for template_choice in ["standard", "full", "minimal", "academic"]:
        gen_res = client.post(
            "/api/generate",
            json={
                "scan_result": scan_data["scan_result"],
                "detection": scan_data["detection"],
                "template": template_choice,
            },
        )
        assert gen_res.status_code == 200, f"Generate {template_choice} failed: {gen_res.text}"
        readme_text = gen_res.json().get("readme", "")
        assert "# " in readme_text
        if template_choice in ["standard", "full"]:
            assert "## Installation" in readme_text or "## Quick Start" in readme_text

    # Step 3: POST /api/generate-ai (mocked API call for reliable E2E execution)
    monkeypatch.setattr(usagetracker, "check_api_key", lambda: True)
    monkeypatch.setattr(usagetracker, "get_api_key", lambda: "gsk_mockede2ekey1234567890abcdef123456")
    monkeypatch.setattr(
        grok.GrokClient,
        "generate_readme",
        lambda self, **kw: "# AI Synthesized README\n\nGenerated via Groq LPU™\n",
    )
    ai_res = client.post(
        "/api/generate-ai",
        json={
            "scan_result": scan_data["scan_result"],
            "detection": scan_data["detection"],
            "tone": "technical",
        },
    )
    assert ai_res.status_code == 200, f"AI Generate failed: {ai_res.text}"
    assert "Groq LPU" in ai_res.json().get("readme", "")


def test_e2e_web_github_profile_presets(monkeypatch):
    """E2E Test: GitHub Profile endpoint across all 4 style presets."""
    monkeypatch.setattr(usagetracker, "check_api_key", lambda: True)
    monkeypatch.setattr(usagetracker, "get_api_key", lambda: "gsk_mockede2ekey1234567890abcdef123456")
    user_mock = lambda *a, **kw: {"name": "Rosh Hellwett", "bio": "E2E Web Architect", "public_repos": 128}
    repos_mock = lambda *a, **kw: [{"name": "projectreadmegen", "language": "Python"}, {"name": "studio-ui", "language": "TypeScript"}]
    stats_mock = lambda *a, **kw: {"Python": 70.0, "TypeScript": 30.0}
    monkeypatch.setattr(github_profile, "fetch_github_user", user_mock)
    monkeypatch.setattr(server, "fetch_github_user", user_mock)
    monkeypatch.setattr(github_profile, "fetch_user_repos", repos_mock)
    monkeypatch.setattr(server, "fetch_user_repos", repos_mock)
    monkeypatch.setattr(github_profile, "calculate_language_stats", stats_mock)
    monkeypatch.setattr(server, "calculate_language_stats", stats_mock)
    profile_gen_mock = lambda **kwargs: f"# @{kwargs['username']} — {kwargs['style'].upper()} Preset\n\nBio: {kwargs['user_data']['bio']}\n"
    monkeypatch.setattr(github_profile, "generate_readme_content", profile_gen_mock)
    monkeypatch.setattr(server, "generate_profile_readme_content", profile_gen_mock)

    for preset in ["professional", "stylish", "unique", "basic"]:
        res = client.post(
            "/api/github-profile",
            json={"username": "roshhellwett", "style": preset},
        )
        assert res.status_code == 200, f"Preset {preset} failed: {res.text}"
        data = res.json()
        assert data["status"] == "success"
        assert data["style_used"] == preset
        assert data["user_data"]["name"] == "Rosh Hellwett"
        assert preset.upper() in data["readme"]
        assert "E2E Web Architect" in data["readme"]
        assert data["languages"]["Python"] == 70.0


def test_e2e_web_atomic_key_synchronization():
    """E2E Test: Atomic key synchronization between REST API endpoint and usagetracker state."""
    test_key = "gsk_webe2etestkey1234567890abcdef1234567890"

    try:
        # Set API key via POST /api/key
        res = client.post("/api/key", json={"api_key": test_key})
        assert res.status_code == 200
        assert res.json().get("status") == "success"

        # Verify status endpoint reflects active configuration
        status_res = client.get("/api/status")
        assert status_res.status_code == 200
        assert status_res.json().get("api_key_configured") is True

        # Verify underlying engine sees the key immediately
        assert usagetracker.get_api_key() == test_key

    finally:
        # Clean up key cleanly
        usagetracker.clear_api_key()
        assert usagetracker.get_api_key() is None
