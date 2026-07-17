import os
import pytest
from typer.testing import CliRunner
from projectreadmegen.cli import app
from projectreadmegen import usagetracker

runner = CliRunner()


def test_status_command():
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "System Diagnostics" in result.stdout
    assert "Engine Version" in result.stdout


def test_config_show_command():
    result = runner.invoke(app, ["config", "--show"])
    assert result.exit_code == 0
    assert "Active Configuration Settings" in result.stdout
    assert "Storage Path" in result.stdout


def test_config_set_and_remove_key():
    test_key = "gsk_testkey_1234567890abcdef1234567890"
    # Set key via CLI command
    result = runner.invoke(app, ["config", "--key", test_key])
    assert result.exit_code == 0
    assert "Groq API Key persisted atomically" in result.stdout
    assert usagetracker.get_api_key() == test_key
    assert os.environ["GROQ_API_KEY"] == test_key

    # Check status reflects the key
    status_result = runner.invoke(app, ["status"])
    assert status_result.exit_code == 0
    assert "Active (" in status_result.stdout

    # Remove key
    rem_result = runner.invoke(app, ["config", "--remove-key"])
    assert rem_result.exit_code == 0
    assert "Groq API Key removed" in rem_result.stdout
    assert usagetracker.get_api_key() is None
