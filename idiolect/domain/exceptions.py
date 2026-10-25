class IdiolectException(Exception):
    """Base exception for Idiolect."""
    pass


class ImproperlyConfigured(IdiolectException):
    """Raised when a component is incorrectly configured."""
    pass
