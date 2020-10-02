from .base import PublicDataStorage
from .error import PublicDataStorageNotFoundError

import requests
from aiohttp import ClientSession, FormData

DATA_VAULT = "http://ocadatavault/api/v1/files"


class DataVault(PublicDataStorage):
    def __init__(self):
        super().__init__()

    async def read(self, id: str) -> str:
        """
        Returns: None on record not found
        """
        url = DATA_VAULT + "/" + id
        print("URL: ", url)

        async with ClientSession() as session:
            result = await session.get(url)
            result = await result.text()
            print(result)

        return result

    async def save(self, record: str) -> str:
        data = FormData()
        data.add_field("file", record, filename="data", content_type="application/json")

        result = None
        async with ClientSession() as session:
            result = await session.post(url=DATA_VAULT, data=data)
            result = await result.text()
            print(result)

        return result

    async def DEBUGread_all(self):
        async with ClientSession() as session:
            result = await session.get(DATA_VAULT)
            result = await result.text()
            print(result)

        return result