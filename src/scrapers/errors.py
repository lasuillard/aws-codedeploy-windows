class ScrapingError(Exception):
    """Base class for scraping errors."""


class UnfulfilledRequirementError(ScrapingError):
    """Raised when a requirement is not fulfilled."""


class AuthenticationError(ScrapingError):
    """Raised when authentication fails."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when provided credentials are invalid."""


class ContextNotInitializedError(ScrapingError):
    """Tried to access contextual properties before initialization."""
