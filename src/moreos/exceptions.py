"""Module containing all exceptions for moreos."""


class MoreosError(Exception):
    """Base-class for all exceptions raised by moreos."""

    pass


class ParsingError(MoreosError):
    """Error raised when there's an error parsing a cookie."""

    pass


class StorageBackendError(MoreosError):
    """Base error for exceptions raised from Storage backends."""

    pass


class ConflictError(StorageBackendError):
    """The backend encountered a conflict saving a cookie."""

    pass
