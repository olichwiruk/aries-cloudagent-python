from .base import BasePersonalDataStorage
from .error import PersonalDataStorageNotFoundError

import uuid
import hashlib


class LocalPersonalDataStorage(BasePersonalDataStorage):
    def __init__(self):
        super().__init__()
        self.storage = {}
        self.preview_settings = (
            {
                "oca_schema_namespace": "pds",
                "oca_schema_dri": "3Fb68s1EPcX4HZhhT23HXrYpuMfcZdreD8xNmEMDc6nC",
            },
        )
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