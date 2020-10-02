from ..core.error import BaseError


class PublicDataStorageError(BaseError):
    """Base class for Storage errors."""


class PublicDataStorageNotFoundError(PublicDataStorageError):
    """Record not found in storage."""


class PublicDataStorageDuplicateError(PublicDataStorageError):
    """Duplicate record found in storage."""


class PublicDataStorageSearchError(PublicDataStorageError):
    """General exception during record search."""
