import pytest
from projectreadmegen.exceptions import (
    ProjectReadmeGenException,
    InvalidPathError,
    AccessDeniedError,
    PermissionError,
    InvalidConfigError,
    APIError,
    FileOperationError,
    TemplateNotFoundError,
    ConfigurationError,
    GitHubAPIError,
    GitHubValidationError,
)


def test_base_exception():
    exc = ProjectReadmeGenException("technical", "user friendly")
    assert exc.message == "technical"
    assert exc.user_message == "user friendly"


def test_base_exception_default_user_message():
    exc = ProjectReadmeGenException("only message")
    assert exc.message == "only message"
    assert exc.user_message == "only message"


def test_invalid_path_error():
    exc = InvalidPathError("bad path", "Path not found")
    assert isinstance(exc, ProjectReadmeGenException)
    assert exc.message == "bad path"


def test_access_denied_error():
    exc = AccessDeniedError("no access")
    assert isinstance(exc, ProjectReadmeGenException)


def test_permission_error_alias():
    assert PermissionError is AccessDeniedError


def test_invalid_config_error():
    exc = InvalidConfigError("bad config")
    assert isinstance(exc, ProjectReadmeGenException)


def test_api_error():
    exc = APIError("api failed")
    assert isinstance(exc, ProjectReadmeGenException)


def test_file_operation_error():
    exc = FileOperationError("file error")
    assert isinstance(exc, ProjectReadmeGenException)


def test_template_not_found_error():
    exc = TemplateNotFoundError("template missing")
    assert isinstance(exc, ProjectReadmeGenException)


def test_configuration_error():
    exc = ConfigurationError("config broken")
    assert isinstance(exc, ProjectReadmeGenException)


def test_github_api_error():
    exc = GitHubAPIError("github error")
    assert isinstance(exc, APIError)
    assert isinstance(exc, ProjectReadmeGenException)


def test_github_validation_error():
    exc = GitHubValidationError("invalid username")
    assert isinstance(exc, InvalidConfigError)
    assert isinstance(exc, ProjectReadmeGenException)
