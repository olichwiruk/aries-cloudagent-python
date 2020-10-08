from ..core.error import BaseError


class PersonalDataStorageError(BaseError):
    """Base class for Storage errors."""


class PersonalDataStorageNotFoundError(PersonalDataStorageError):
    """Record not found in storage."""


class PersonalDataStorageDuplicateError(PersonalDataStorageError):
    """Duplicate record found in storage."""


class PersonalDataStorageSearchError(PersonalDataStorageError):
    """General exception during record search."""


class PersonalDataStorageLackingConfigurationError(PersonalDataStorageError):
    """When lack of configuration is detected."""


class PersonalDataStorageInvalidConfigurationError(PersonalDataStorageError):
    """When configuration contains fields with invalid information."""


class PersonalDataStorageServerError(PersonalDataStorageError):
    """When configuration contains fields with invalid information."""