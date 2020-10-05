from ..core.error import BaseError


class PublicDataStorageError(BaseError):
    """Base class for Storage errors."""


class PublicDataStorageNotFoundError(PublicDataStorageError):
    """Record not found in storage."""


class PublicDataStorageDuplicateError(PublicDataStorageError):
    """Duplicate record found in storage."""


class PublicDataStorageSearchError(PublicDataStorageError):
    """General exception during record search."""


class PublicDataStorageLackingConfigurationError(PublicDataStorageError):
    """When lack of configuration is detected."""


class PublicDataStorageInvalidConfigurationError(PublicDataStorageError):
    """When configuration contains fields with invalid information."""


class PublicDataStorageServerError(PublicDataStorageError):
    """When configuration contains fields with invalid information."""