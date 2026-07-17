"""End-to-End CLI Lifecycle Workflow Tests for Project README Gen 5.1.13.

Tests full end-to-end execution paths right from terminal commands down to
disk persistence, template compilation, and atomic credential synchronization.
"""

import os
from pathlib import Path
from typer.testing import CliRunner

from projectreadmegen import cli, usagetracker

runner = CliRunner()


def test_e2e_cli_generate_workflow(tmp_path: Path):
    """E2E Test: Full scan and README generation on a sample project structure."""
    # Create sample project structure inside temporary directory
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('Hello E2E Studio')\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("typer>=0.12\nfastapi>=0.100\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Old Readme to Overwrite\n", encoding="utf-8")

    # Execute CLI generate workflow
    result = runner.invoke(
        cli.app,
        ["generate", str(tmp_path), "--template", "full", "--force"],
    )
    assert result.exit_code == 0, f"Generate failed: {result.stdout}"
    assert "Documentation Architecture Generated Successfully" in result.stdout

    # Verify generated output on disk
    readme_path = tmp_path / "README.md"
    assert readme_path.exists()
    content = readme_path.read_text(encoding="utf-8")
    assert "# " in content
    assert "## Installation" in content
    assert "## Tech Stack" in content
    assert "Python" in content


def test_e2e_cli_profile_workflow(tmp_path: Path, monkeypatch):
    """E2E Test: Direct CLI generation of a bento-style GitHub Profile README."""
    # Mock API verification and network calls for reliable offline E2E execution
    monkeypatch.setattr(usagetracker, "check_api_key", lambda: True)
    monkeypatch.setattr(
        cli.github_profile,
        "validate_github_username",
        lambda u: (True, ""),
    )
    monkeypatch.setattr(
        cli.github_profile,
        "fetch_github_user",
        lambda u, t: {"name": "Rosh Hellwett", "bio": "E2E Studio Creator", "public_repos": 42},
    )
    monkeypatch.setattr(
        cli.github_profile,
        "fetch_user_repos",
        lambda u, t: [{"name": "projectreadmegen", "language": "Python"}],
    )
    monkeypatch.setattr(
        cli.github_profile,
        "calculate_language_stats",
        lambda r: {"Python": 100.0},
    )
    monkeypatch.setattr(
        cli.github_profile,
        "generate_readme_content",
        lambda **kwargs: "# Rosh Hellwett\n\n![Stats](https://github-readme-stats.vercel.app/api?username=roshhellwett)\n",
    )

    result = runner.invoke(
        cli.app,
        [
            "profile",
            "-u",
            "roshhellwett",
            "-s",
            "professional",
            "-o",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, f"Profile command failed: {result.stdout}"
    assert "GitHub Profile Architecture Generated Successfully" in result.stdout

    # Verify file saved inside username subfolder
    profile_readme = tmp_path / "roshhellwett" / "README.md"
    assert profile_readme.exists()
    content = profile_readme.read_text(encoding="utf-8")
    assert "roshhellwett" in content.lower()
    assert "github-readme-stats" in content


def test_e2e_cli_config_and_status_sync():
    """E2E Test: Atomic credential sync across config command, environment, and status."""
    test_key = "gsk_e2etestkey_1234567890abcdef1234567890"
    test_token = "ghp_e2etesttoken_1234567890abcdef1234567"

    try:
        # Set credentials via CLI
        cfg_res = runner.invoke(cli.app, ["config", "--key", test_key, "--token", test_token])
        assert cfg_res.exit_code == 0
        assert "Groq API Key persisted atomically" in cfg_res.stdout
        assert "GitHub API Token persisted atomically" in cfg_res.stdout

        # Verify exact environment variable population
        assert os.environ.get("GROQ_API_KEY") == test_key
        assert os.environ.get("GITHUB_TOKEN") == test_token
        assert usagetracker.get_api_key() == test_key
        assert usagetracker.get_github_token() == test_token

        # Check status dashboard reflects both credentials
        status_res = runner.invoke(cli.app, ["status"])
        assert status_res.exit_code == 0
        assert "Active (" in status_res.stdout

    finally:
        # Cleanup credentials cleanly
        rem_res = runner.invoke(cli.app, ["config", "--remove-key", "--remove-token"])
        assert rem_res.exit_code == 0
        assert usagetracker.get_api_key() is None
