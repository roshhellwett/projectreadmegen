"""Smoke Test Suite for Project README Gen 6.0.0.

Provides rapid sanity checks covering package integrity, critical imports,
CLI responsiveness, and REST API/SPA static delivery health.
"""

import pytest
from typer.testing import CliRunner
from fastapi.testclient import TestClient

import projectreadmegen
from projectreadmegen import (
    __version__,
    cli,
    detector,
    generator,
    github_profile,
    grok,
    scanner,
    server,
    usagetracker,
)

runner = CliRunner()
client = TestClient(server.app)


def test_package_version_and_imports():
    """Verify package version consistency and clean module imports."""
    assert __version__ == "6.0.0"
    assert cli.app is not None
    assert server.app is not None
    assert hasattr(scanner, "scan_directory")
    assert hasattr(detector, "detect_stack")
    assert hasattr(generator, "generate_readme")
    assert hasattr(github_profile, "fetch_github_user")
    assert hasattr(grok, "generate_ai_readme")
    assert hasattr(usagetracker, "get_unified_status_dict")


def test_cli_smoke_invocation():
    """Verify fast CLI command responsiveness and basic flags."""
    # Test --help
    help_res = runner.invoke(cli.app, ["--help"])
    assert help_res.exit_code == 0
    assert "projectreadmegen" in help_res.stdout
    assert "status" in help_res.stdout
    assert "web" in help_res.stdout

    # Test status
    status_res = runner.invoke(cli.app, ["status"])
    assert status_res.exit_code == 0
    assert "System Diagnostics" in status_res.stdout

    # Test version
    result = runner.invoke(cli.app, ["--version"])
    assert result.exit_code == 0
    assert "6.0.0" in result.stdout


def test_server_health_smoke():
    """Verify FastAPI server initializes and /api/status responds immediately."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "api_key_configured" in data
    assert "github_token_configured" in data
    assert "storage_path" in data
    assert "credits_message" in data


def test_static_spa_delivery_smoke():
    """Verify root / delivers our packaged Obsidian SPA index.html cleanly."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "<title>" in response.text or "<div id=\"root\">" in response.text
