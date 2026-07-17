"""
Production-grade exception classes for better error handling and user messaging.

All application exceptions inherit from ProjectReadmeGenException so that
CLI and API error handlers can catch them uniformly.
"""


class ProjectReadmeGenException(Exception):
    """Base exception for all projectreadmegen errors."""

    def __init__(self, message: str, user_message: str | None = None):
        """
        Initialize exception with both technical and user-friendly messages.

        Args:
            message: Technical error message for logging
            user_message: User-friendly message for display (defaults to message)
        """
        super().__init__(message)
        self.message = message
        self.user_message = user_message or message


class InvalidPathError(ProjectReadmeGenException):
    """Raised when a provided path is invalid or inaccessible."""

    pass


class AccessDeniedError(ProjectReadmeGenException):
    """Raised when the user lacks permission to access a path or file.

    NOTE: Previously named ``PermissionError``, renamed to avoid shadowing
    the Python builtin ``PermissionError``.
    """

    pass


# Keep the old name available as an alias for backwards compatibility,
# but new code should use AccessDeniedError.
PermissionError = AccessDeniedError  # type: ignore[assignment]


class InvalidConfigError(ProjectReadmeGenException):
    """Raised when configuration is invalid."""

    pass


class APIError(ProjectReadmeGenException):
    """Raised when external API call fails (Groq, etc.)."""

    pass


class FileOperationError(ProjectReadmeGenException):
    """Raised when file operations fail."""

    pass


class TemplateNotFoundError(ProjectReadmeGenException):
    """Raised when a required template is not found."""

    pass


class ConfigurationError(ProjectReadmeGenException):
    """Raised when configuration loading or validation fails."""

    pass


# ---------------------------------------------------------------------------
# GitHub-specific exceptions (integrated into the hierarchy)
# ---------------------------------------------------------------------------


class GitHubAPIError(APIError):
    """Raised when a GitHub REST API call fails.

    Inherits from APIError so that generic API error handlers catch it too.
    """

    pass


class GitHubValidationError(InvalidConfigError):
    """Raised when GitHub-related input validation fails (username, URL, etc.).

    Inherits from InvalidConfigError for consistency with other validation errors.
    """

    pass
