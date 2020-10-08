from .base import BasePersonalDataStorage
from .error import PersonalDataStorageNotFoundError

import uuid


class LocalPersonalDataStorage(BasePersonalDataStorage):
    def __init__(self):
        super().__init__()
        self.storage = {}
        self.settings = {"no_configuration_needed": "yes"}

    async def load(self, id: str) -> str:
        """
        returns: None, on record not found
        """
        result = self.storage.get(id)

        return result

    async def save(self, record: str) -> str:
        result = str(uuid.uuid4())
        self.storage[result] = record

        return result