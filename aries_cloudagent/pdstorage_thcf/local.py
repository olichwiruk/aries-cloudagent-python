from .base import BasePersonalDataStorage
from .error import PDSNotFoundError
from .api import encode


class LocalPersonalDataStorage(BasePersonalDataStorage):
    def __init__(self):
        super().__init__()
        self.storage = {}
        self.preview_settings = {
            "oca_schema_namespace": "pds",
            "oca_schema_dri": "3Fb68s1EPcX4HZhhT23HXrYpuMfcZdreD8xNmEMDc6nC",
        }

        self.settings = {"no_configuration_needed": "yes"}

    async def load(self, id: str) -> str:
        """
        returns: None, on record not found
        """
        result = self.storage.get(id)

        return result

    async def save(self, record: str, metadata: str) -> str:
        result = encode(record)
        self.storage[result] = record

        return result

    async def load_multiple(
        self, *, table: str = None, oca_schema_base_dri: str = None
    ) -> str:

        assert not "Load multiple not supported by active PDS"

    async def ping(self) -> [bool, str]:
        return [True, None]
