"""
Production-grade exception classes for better error handling and user messaging.
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


class PermissionError(ProjectReadmeGenException):
    """Raised when the user lacks permission to access a path or file."""

    pass


class InvalidConfigError(ProjectReadmeGenException):
    """Raised when configuration is invalid."""

    pass


class APIError(ProjectReadmeGenException):
    """Raised when external API call fails."""

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
