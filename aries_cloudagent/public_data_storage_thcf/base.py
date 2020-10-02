from abc import ABC, abstractmethod
from .error import PublicDataStorageDuplicateError, PublicDataStorageNotFoundError


class PublicDataStorage(ABC):
    def __init__(self):
        self.settings = {}

    @abstractmethod
    async def save(self, record: str) -> str:
        """
        Returns: saved data id, (should maybe return None on key not found?)

        """

    @abstractmethod
    async def read(self, id: str) -> str:
        """
        Returns: data represented by id
        """

    def __repr__(self) -> str:
        """
        Return a human readable representation of this class.

        Returns:
            A human readable string for this class

        """
        return "<{}>".format(self.__class__.__name__)
