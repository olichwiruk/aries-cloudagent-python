from abc import ABC, abstractmethod
from .error import PersonalDataStorageDuplicateError, PersonalDataStorageNotFoundError


class BasePersonalDataStorage(ABC):
    def __init__(self):
        self.settings = {}
        self.preview_settings = {}

    @abstractmethod
    async def save(self, record: str) -> str:
        """
        Returns: saved data id, (should maybe return None on key not found?)

        """

    @abstractmethod
    async def load(self, id: str) -> str:
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
