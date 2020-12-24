from ..core.error import BaseError


class PDSError(BaseError):
    """Base class for Storage errors."""


class PDSNotFoundError(PDSError):
    """
    Class of PDS not found.
    This can be thrown when there is no active PDS or PDS type was not found.
    """


class PDSRecordNotFoundError(PDSError):
    """Record not found in storage"""
