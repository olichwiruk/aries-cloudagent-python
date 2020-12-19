from ..core.error import BaseError


class PersonalDataStorageError(BaseError):
    """Base class for Storage errors."""


class PersonalDataStorageNotFoundError(BaseError):
    """Class for record not found in storage"""
