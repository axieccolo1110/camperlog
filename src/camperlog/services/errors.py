class ValidationError(ValueError):
    """A business rule was violated. The message is shown to the user (German)."""


class NotFoundError(LookupError):
    """A referenced object does not exist. The message is shown to the user (German)."""
