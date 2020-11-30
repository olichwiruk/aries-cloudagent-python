from .base import BasePersonalDataStorage
from .api import encode
from .error import *

import json
import logging
from urllib.parse import urlparse

from aiohttp import ClientSession, FormData

LOGGER = logging.getLogger(__name__)


class OwnYourDataVault(BasePersonalDataStorage):
    def __init__(self):
        super().__init__()
        self.api_url = None
        self.token = None
        self.preview_settings = {
            "oca_schema_namespace": "pds",
            "oca_schema_dri": "9bABtmHu628Ss4oHmyTU5gy7QB1VftngewTmh7wdmN1j",
        }

    async def update_token(self):
        # TODO: Add timestamp check because token expires
        # if self.token != None:
        #     return

        parsed_url = urlparse(self.settings.get("api_url"))
        self.api_url = '{url.scheme}://{url.netloc}'.format(url=parsed_url)
        client_id = self.settings.get("client_id")
        client_secret = self.settings.get("client_secret")
        grant_type = self.settings.get("grant_type", "client_credentials")
        scope = self.settings.get("scope")

        if self.api_url is None:
            raise PersonalDataStorageLackingConfigurationError(
                "Please configure the plugin, api_url is empty"
            )
        if client_id == None:
            raise PersonalDataStorageLackingConfigurationError(
                "Please configure the plugin, Client_id is empty"
            )
        if client_secret == None:
            raise PersonalDataStorageLackingConfigurationError(
                "Please configure the plugin, Client_secret is empty"
            )

        async with ClientSession() as session:
            body = {
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": grant_type
            }
            if scope is not None:
                body["scope"] = scope
            result = await session.post(
                self.api_url + "/oauth/token",
                json=body,
            )
            if result.status != 200:
                raise PersonalDataStorageServerError(
                    "Server Error, Could be that the connection is invalid or some other unforseen error, check if the server is up"
                )

            result = await result.text()
            token = json.loads(result)
            self.token = token
            LOGGER.info("update token: %s", self.token)

    async def load(self, dri: str) -> str:
        """
        TODO: Errors checking
        """
        await self.update_token()

        url = f"{self.api_url}/api/data/{dri}?p=dri&f=plain"
        async with ClientSession() as session:
            result = await session.get(
                url, headers={"Authorization": "Bearer " + self.token["access_token"]}
            )
            result_str = await result.text()
            result_dict = json.loads(result_str)
            LOGGER.info("Result of GET request %s", result_str)

        return result_str

    async def save(self, record: str, metadata: str) -> str:
        oyd_repo = self.settings.get("repo")
        dri_value = encode(record)
        meta = json.loads(metadata)
        await self.update_token()
        async with ClientSession() as session:
            body = {
                "content": json.loads(record),
                "dri": dri_value,
                "table_name": oyd_repo if oyd_repo is not None else "dip.data",
            }
            if meta["oca_schema_dri"]:
                body["schema_dri"] = meta["oca_schema_dri"]
            result = await session.post(
                f"{self.api_url}/api/data",
                headers={"Authorization": "Bearer " + self.token["access_token"]},
                json=body,
            )
            result = await result.text()
            result = json.loads(result)
            LOGGER.info("Result of POST request %s", result)

        return dri_value
