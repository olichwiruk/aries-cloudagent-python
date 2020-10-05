from .base import PublicDataStorage
from .error import PublicDataStorageNotFoundError

import uuid


class LocalDataStorage(PublicDataStorage):
    def __init__(self):
        super().__init__()
        self.storage = {}
        self.settings = {"no_configuration": "needed"}

    async def read(self, id: str) -> str:
        """
        returns: None, on record not found
        """
        result = self.storage.get(id)

        return result

    async def save(self, record: str) -> str:
        result = str(uuid.uuid4())
        self.storage[result] = record

        return result