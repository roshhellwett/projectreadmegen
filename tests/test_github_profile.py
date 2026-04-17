# tests/test_github_profile.py

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from projectreadmegen import github_profile


class TestValidation:
    """Test validation functions."""

    def test_validate_username_valid_simple(self):
        """Test valid simple username."""
        is_valid, error = github_profile.validate_github_username("testuser")
        assert is_valid is True
        assert error == ""

    def test_validate_username_valid_with_hyphen(self):
        """Test valid username with hyphen."""
        is_valid, error = github_profile.validate_github_username("test-user")
        assert is_valid is True
        assert error == ""

    def test_validate_username_valid_numbers(self):
        """Test valid username with numbers."""
        is_valid, error = github_profile.validate_github_username("test123")
        assert is_valid is True
        assert error == ""

    def test_validate_username_empty(self):
        """Test empty username is invalid."""
        is_valid, error = github_profile.validate_github_username("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_validate_username_starts_with_hyphen(self):
        """Test username starting with hyphen is invalid."""
        is_valid, error = github_profile.validate_github_username("-testuser")
        assert is_valid is False
        assert "start" in error.lower()

    def test_validate_username_ends_with_hyphen(self):
        """Test username ending with hyphen is invalid."""
        is_valid, error = github_profile.validate_github_username("testuser-")
        assert is_valid is False
        assert "end" in error.lower()

    def test_validate_username_consecutive_hyphens(self):
        """Test username with consecutive hyphens is invalid."""
        is_valid, error = github_profile.validate_github_username("test--user")
        assert is_valid is False
        assert "consecutive" in error.lower()

    def test_validate_username_too_long(self):
        """Test username over 39 characters is invalid."""
        is_valid, error = github_profile.validate_github_username("a" * 40)
        assert is_valid is False
        assert "39" in error

    def test_validate_username_with_special_chars(self):
        """Test username with special characters is invalid."""
        is_valid, error = github_profile.validate_github_username("test@user!")
        assert is_valid is False

    def test_validate_url_valid(self):
        """Test valid GitHub URL."""
        is_valid, username = github_profile.validate_github_url(
            "https://github.com/testuser"
        )
        assert is_valid is True
        assert username == "testuser"

    def test_validate_url_valid_http(self):
        """Test valid GitHub URL with http."""
        is_valid, username = github_profile.validate_github_url(
            "http://github.com/testuser"
        )
        assert is_valid is True
        assert username == "testuser"

    def test_validate_url_valid_short(self):
        """Test valid short GitHub URL."""
        is_valid, username = github_profile.validate_github_url("github.com/testuser")
        assert is_valid is True
        assert username == "testuser"

    def test_validate_url_with_trailing_slash(self):
        """Test GitHub URL with trailing slash."""
        is_valid, username = github_profile.validate_github_url(
            "https://github.com/testuser/"
        )
        assert is_valid is True
        assert username == "testuser"

    def test_validate_url_invalid(self):
        """Test invalid GitHub URL."""
        is_valid, username = github_profile.validate_github_url(
            "https://example.com/testuser"
        )
        assert is_valid is False
        assert username == ""

    def test_validate_url_empty(self):
        """Test empty URL is invalid."""
        is_valid, username = github_profile.validate_github_url("")
        assert is_valid is False
        assert username == ""

    def test_extract_username_from_url(self):
        """Test extracting username from URL."""
        username = github_profile.extract_username_from_url(
            "https://github.com/testuser"
        )
        assert username == "testuser"


class TestLanguageStats:
    """Test language statistics calculation."""

    def test_calculate_language_stats_empty(self):
        """Test empty repos list."""
        result = github_profile.calculate_language_stats([])
        assert result == {}

    def test_calculate_language_stats_single_language(self):
        """Test repos with single language."""
        repos = [
            {"language": "Python"},
            {"language": "Python"},
            {"language": "Python"},
        ]
        result = github_profile.calculate_language_stats(repos)
        assert result == {"Python": 100}

    def test_calculate_language_stats_multiple_languages(self):
        """Test repos with multiple languages."""
        repos = [
            {"language": "Python"},
            {"language": "Python"},
            {"language": "JavaScript"},
        ]
        result = github_profile.calculate_language_stats(repos)
        assert result["Python"] == 66
        assert result["JavaScript"] == 33

    def test_calculate_language_stats_with_none(self):
        """Test repos with None language."""
        repos = [
            {"language": "Python"},
            {"language": None},
            {"language": "JavaScript"},
        ]
        result = github_profile.calculate_language_stats(repos)
        assert "Python" in result
        assert "JavaScript" in result

    def test_calculate_language_stats_sorted(self):
        """Test languages are sorted by percentage."""
        repos = [
            {"language": "Python"},
            {"language": "Python"},
            {"language": "Python"},
            {"language": "JavaScript"},
            {"language": "Go"},
        ]
        result = github_profile.calculate_language_stats(repos)
        keys = list(result.keys())
        assert keys[0] == "Python"


class TestProfileContext:
    """Test profile context building."""

    def test_build_profile_context_minimal(self):
        """Test building context with minimal data."""
        context = github_profile.build_profile_context(
            username="testuser",
            profile_url="https://github.com/testuser",
            user_data=None,
            repos=None,
            languages=None,
            style="basic",
        )
        assert "testuser" in context
        assert "basic" in context

    def test_build_profile_context_full(self):
        """Test building context with full data."""
        user_data = {
            "name": "Test User",
            "bio": "A test developer",
            "company": "Test Corp",
            "location": "Test City",
            "public_repos": 10,
            "followers": 100,
            "following": 50,
        }
        repos = [
            {
                "name": "test-repo",
                "description": "A test repository",
                "stargazers_count": 50,
                "language": "Python",
            }
        ]
        languages = {"Python": 100}

        context = github_profile.build_profile_context(
            username="testuser",
            profile_url="https://github.com/testuser",
            user_data=user_data,
            repos=repos,
            languages=languages,
            style="professional",
        )

        assert "Test User" in context
        assert "test-repo" in context
        assert "Python" in context
        assert "professional" in context


class TestStylePrompts:
    """Test style prompt generation."""

    def test_get_style_prompt_basic(self):
        """Test getting basic style prompt."""
        prompt = github_profile.get_style_prompt("basic")
        assert "clean" in prompt.lower()
        assert "professional" in prompt.lower()

    def test_get_style_prompt_professional(self):
        """Test getting professional style prompt."""
        prompt = github_profile.get_style_prompt("professional")
        assert "career" in prompt.lower()

    def test_get_style_prompt_stylish(self):
        """Test getting stylish style prompt."""
        prompt = github_profile.get_style_prompt("stylish")
        assert "visually" in prompt.lower() or "stunning" in prompt.lower()

    def test_get_style_prompt_unique(self):
        """Test getting unique style prompt."""
        prompt = github_profile.get_style_prompt("unique")
        assert "creative" in prompt.lower() or "memorable" in prompt.lower()

    def test_get_style_prompt_default(self):
        """Test default style prompt falls back to basic."""
        prompt = github_profile.get_style_prompt("nonexistent")
        assert "clean" in prompt.lower()


class TestOutputFolder:
    """Test output folder creation."""

    def test_create_output_folder_new(self, tmp_path):
        """Test creating new output folder."""
        success, result = github_profile.create_output_folder("testuser", str(tmp_path))
        assert success is True
        assert "testuser" in result

    def test_create_output_folder_already_exists(self, tmp_path):
        """Test creating folder that already exists."""
        success, result = github_profile.create_output_folder("testuser", str(tmp_path))
        assert success is True

        success2, result2 = github_profile.create_output_folder(
            "testuser", str(tmp_path)
        )
        assert success2 is True

    def test_create_output_folder_path_not_exist(self, tmp_path):
        """Test creating folder in non-existent path."""
        success, result = github_profile.create_output_folder(
            "testuser", str(tmp_path / "nonexistent")
        )
        assert success is True


class TestReadmeExists:
    """Test README existence checking."""

    def test_check_readme_exists_false(self, tmp_path):
        """Test README does not exist."""
        exists, path = github_profile.check_readme_exists(str(tmp_path))
        assert exists is False

    def test_check_readme_exists_true(self, tmp_path):
        """Test README exists."""
        readme = tmp_path / "README.md"
        readme.write_text("# Test")
        exists, path = github_profile.check_readme_exists(str(tmp_path))
        assert exists is True


class TestSaveReadme:
    """Test README saving."""

    def test_save_github_readme(self, tmp_path):
        """Test saving README."""
        content = "# Test README"
        success, result = github_profile.save_github_readme(
            content, str(tmp_path), "testuser"
        )
        assert success is True
        assert "README.md" in result

        readme_file = tmp_path / "README.md"
        assert readme_file.exists()
        assert readme_file.read_text() == content


class TestMockAPIFetch:
    """Test API fetching with mocking."""

    @patch("projectreadmegen.github_profile.requests.get")
    def test_fetch_github_user_success(self, mock_get):
        """Test successful user fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "login": "testuser",
            "name": "Test User",
            "bio": "A test developer",
            "public_repos": 10,
            "followers": 100,
            "following": 50,
        }
        mock_get.return_value = mock_response

        result = github_profile.fetch_github_user("testuser")
        assert result is not None
        assert result["login"] == "testuser"
        assert result["name"] == "Test User"

    @patch("projectreadmegen.github_profile.requests.get")
    def test_fetch_github_user_not_found(self, mock_get):
        """Test user not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = github_profile.fetch_github_user("nonexistent")
        assert result is None

    @patch("projectreadmegen.github_profile.requests.get")
    def test_fetch_github_user_rate_limit(self, mock_get):
        """Test rate limit error."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        with pytest.raises(github_profile.GitHubAPIError) as exc_info:
            github_profile.fetch_github_user("testuser")
        assert "rate limit" in str(exc_info.value).lower()

    @patch("projectreadmegen.github_profile.requests.get")
    def test_fetch_user_repos_success(self, mock_get):
        """Test successful repos fetch."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = [
            {
                "name": "repo1",
                "description": "First repo",
                "language": "Python",
                "stargazers_count": 50,
                "forks_count": 10,
                "topics": ["python", "api"],
                "html_url": "https://github.com/testuser/repo1",
                "homepage": None,
                "fork": False,
                "archived": False,
            }
        ]
        mock_get.return_value = mock_response

        repos = github_profile.fetch_user_repos("testuser")
        assert len(repos) == 1
        assert repos[0]["name"] == "repo1"
        assert repos[0]["language"] == "Python"


class TestGenerateReadmeContent:
    """Test README content generation."""

    @patch("projectreadmegen.github_profile.usagetracker.get_api_key")
    @patch("projectreadmegen.grok.GrokClient")
    def test_generate_readme_content(self, mock_client, mock_get_key):
        """Test generating README content."""
        mock_get_key.return_value = "test_api_key"

        mock_client_instance = MagicMock()
        mock_client_instance.generate_readme.return_value = "# Generated README"
        mock_client.return_value = mock_client_instance

        result = github_profile.generate_readme_content(
            username="testuser",
            profile_url="https://github.com/testuser",
            style="basic",
        )
        assert "# Generated README" in result

    @patch("projectreadmegen.github_profile.usagetracker.get_api_key")
    def test_generate_readme_content_no_api_key(self, mock_get_key):
        """Test error when no API key."""
        mock_get_key.return_value = None

        with pytest.raises(github_profile.GitHubValidationError) as exc_info:
            github_profile.generate_readme_content(
                username="testuser",
                profile_url="https://github.com/testuser",
                style="basic",
            )
        assert "API key" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
