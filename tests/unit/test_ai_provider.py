from unittest.mock import MagicMock, patch
import pytest
from projectreadmegen.ai_provider import GroqClient, build_project_context, generate_ai_readme
from projectreadmegen.exceptions import APIError as CustomAPIError


def test_groq_client_no_key():
    client = GroqClient(api_key=None)
    with pytest.raises(CustomAPIError, match="API key not set"):
        client.generate_readme(project_context="test", system_prompt="test")


def test_groq_client_invalid_context():
    client = GroqClient(api_key="gsk_test")
    with pytest.raises(CustomAPIError, match="Invalid project context"):
        client.generate_readme(project_context="", system_prompt="test")


def test_groq_client_invalid_prompt():
    client = GroqClient(api_key="gsk_test")
    with pytest.raises(CustomAPIError, match="Invalid system prompt"):
        client.generate_readme(project_context="test", system_prompt="")


def test_groq_client_empty_response():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = []
    mock_client.chat.completions.create.return_value = mock_response
    client = GroqClient(api_key="gsk_test")
    client.client = mock_client
    with pytest.raises(CustomAPIError, match="Empty response"):
        client.generate_readme(project_context="test", system_prompt="test")


def test_groq_client_success():
    mock_client = MagicMock()
    mock_response = MagicMock()
    choice = MagicMock()
    choice.message.content = "# Generated README\n\nContent here"
    mock_response.choices = [choice]
    mock_client.chat.completions.create.return_value = mock_response
    client = GroqClient(api_key="gsk_test")
    client.client = mock_client
    result = client.generate_readme(project_context="Project context", system_prompt="Write a README")
    assert "# Generated README" in result


def test_groq_client_retry_then_success():
    mock_client = MagicMock()
    from openai import APITimeoutError
    mock_client.chat.completions.create.side_effect = [
        APITimeoutError("timeout"),
        APITimeoutError("timeout"),
        ChoiceResponse("# README after retry"),
    ]
    client = GroqClient(api_key="gsk_test")
    client.client = mock_client
    result = client.generate_readme(project_context="test", system_prompt="test")
    assert "# README after retry" in result


class ChoiceResponse:
    def __init__(self, content):
        self.choices = [Choice(content)]


class Choice:
    def __init__(self, content):
        self.message = Message(content)


class Message:
    def __init__(self, content):
        self.content = content


def test_build_project_context():
    scan = {
        "name": "test-project",
        "files": ["main.py", "README.md"],
        "dirs": ["src", "tests"],
        "tree": "├── main.py\n├── src/",
        "has_license": True,
        "has_contributing": False,
    }
    detection = {
        "project_type": "cli-tool",
        "primary_lang": "Python",
        "languages": ["Python"],
        "install_cmd": "pip install .",
        "run_cmd": "python main.py",
    }
    config = {}
    ctx = build_project_context(scan, detection, config)
    assert "test-project" in ctx
    assert "Python" in ctx
    assert "cli-tool" in ctx
    assert "main.py" in ctx
    assert "LICENSE" in ctx


def test_generate_ai_readme_no_key():
    with pytest.raises(CustomAPIError, match="No Groq API key configured"):
        generate_ai_readme({"name": "test"}, {"primary_lang": "Python"}, {})


def test_generate_ai_readme_invalid_data():
    with pytest.raises(CustomAPIError, match="Invalid scan"):
        generate_ai_readme("not a dict", {"primary_lang": "Python"}, {"groq_api_key": "gsk_test"})


@patch("projectreadmegen.ai_provider.GroqClient.generate_readme")
def test_generate_ai_readme_success(mock_gen):
    mock_gen.return_value = "# AI README"
    result = generate_ai_readme(
        {"name": "test", "files": ["a.py"], "dirs": [], "tree": "", "has_license": False, "has_contributing": False},
        {"project_type": "app", "primary_lang": "Python", "languages": ["Python"], "install_cmd": "", "run_cmd": ""},
        {"groq_api_key": "gsk_test"},
    )
    assert result == "# AI README"
