from .base import BasePersonalDataStorage
from .error import PersonalDataStorageNotFoundError

import uuid
import hashlib


class LocalPersonalDataStorage(BasePersonalDataStorage):
    def __init__(self):
        super().__init__()
        self.storage = {}
        self.preview_settings = {"no_configuration_needed": "yes"}
        self.settings = {"no_configuration_needed": "yes"}

    async def load(self, id: str) -> str:
        """
        returns: None, on record not found
        """
        result = self.storage.get(id)

        return result

    async def save(self, record: str) -> str:
        result = hashlib.sha256(record.encode("UTF-8")).hexdigest()
        self.storage[result] = record

        return result