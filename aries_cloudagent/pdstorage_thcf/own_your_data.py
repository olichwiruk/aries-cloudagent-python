from .base import BasePersonalDataStorage
from .api import encode
from .error import PersonalDataStorageError

import json
import logging
from urllib.parse import urlparse

from aiohttp import ClientSession
from aries_cloudagent.aathcf.credentials import assert_type
import time
from collections import OrderedDict

LOGGER = logging.getLogger(__name__)


async def unpack_response(response):
    result: str = await response.text()
    if response.status != 200:
        LOGGER.error("Error Own Your Data PDS", result)
        raise PersonalDataStorageError("Error Own Your Data PDS", result)

    return result


class OwnYourDataVault(BasePersonalDataStorage):
    def __init__(self):
        super().__init__()
        self.api_url = None
        self.token = {"expires_in": "-1000"}
        self.token_timestamp = 0
        self.preview_settings = {
            "oca_schema_namespace": "pds",
            "oca_schema_dri": "9bABtmHu628Ss4oHmyTU5gy7QB1VftngewTmh7wdmN1j",
        }

    async def get_usage_policy(self):
        if self.settings.get("usage_policy") is None:
            await self.update_token()

        return self.settings["usage_policy"]

    async def update_token(self):

        """
        Check if the token expired
        """

        time_elapsed = time.time() - (self.token_timestamp - 10)
        if time_elapsed > float(self.token["expires_in"]):
            print("TOKEN UPDATE", time_elapsed, self.token["expires_in"])

            parsed_url = urlparse(self.settings.get("api_url"))
            self.api_url = "{url.scheme}://{url.netloc}".format(url=parsed_url)
            LOGGER.info("API URL OYD %s", self.api_url)

            client_id = self.settings.get("client_id")
            client_secret = self.settings.get("client_secret")
            grant_type = self.settings.get("grant_type", "client_credentials")
            scope = self.settings.get("scope")

            if self.api_url is None:
                raise PersonalDataStorageError(
                    "Please configure the plugin, api_url is empty"
                )
            if client_id is None:
                raise PersonalDataStorageError(
                    "Please configure the plugin, client_id is empty"
                )
            if client_secret is None:
                raise PersonalDataStorageError(
                    "Please configure the plugin, client_secret is empty"
                )

            async with ClientSession() as session:
                body = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": grant_type,
                }
                if scope is not None:
                    body["scope"] = scope
                result = await session.post(
                    self.api_url + "/oauth/token",
                    json=body,
                )
                result = await unpack_response(result)
                token = json.loads(result)
                self.token = token
                self.token_timestamp = time.time()
                LOGGER.info("update token: %s", self.token)

            """
            Download the usage policy

            """

            url = f"{self.api_url}/api/meta/usage"
            async with ClientSession() as session:
                result = await session.get(
                    url,
                    headers={"Authorization": "Bearer " + self.token["access_token"]},
                )
                result = await unpack_response(result)
                self.settings["usage_policy"] = result
                LOGGER.info("Usage policy %s", self.settings["usage_policy"])

    async def load(self, dri: str) -> str:
        """
        TODO: Errors checking
        """
        assert_type(dri, str)
        await self.update_token()

        url = f"{self.api_url}/api/data/{dri}?p=dri&f=plain"
        async with ClientSession() as session:
            result = await session.get(
                url, headers={"Authorization": "Bearer " + self.token["access_token"]}
            )
            result = await unpack_response(result)
            result_dict: dict = json.loads(result, object_pairs_hook=OrderedDict)
            result_dict = result_dict.get("content")

        if isinstance(result_dict, dict):
            result_dict = json.dumps(result_dict)

        return result_dict

    async def save(self, record: str, metadata: str) -> str:
        """
        meta: {
            "table" - specifies the table name into which save the data
            "oca_schema_dri"
        }
        """
        assert_type(record, str)
        assert_type(metadata, str)
        await self.update_token()

        table = self.settings.get("repo")
        table = table if table is not None else "dip.data"

        meta = json.loads(metadata)
        dri_value = encode(record)

        record = {"content": record}
        record["dri"] = dri_value

        LOGGER.info("OYD save record %s metadata %s", record, meta)
        async with ClientSession() as session:
            """
            Pack request body
            """

            if meta.get("table") is not None:
                table = f"{table}.{meta.get('table')}"

            body = {
                "content": record,
                "dri": dri_value,
                "table_name": table,
                "mime_type": "application/json",
            }

            if meta.get("oca_schema_dri") is not None:
                record["oca_schema_dri"] = meta["oca_schema_dri"]
                body["schema_dri"] = meta["oca_schema_dri"]

            """
            Request
            """

            url = f"{self.api_url}/api/data"
            response = await session.post(
                url,
                headers={"Authorization": "Bearer " + self.token["access_token"]},
                json=body,
            )
            result = await unpack_response(response)
            result = json.loads(result)
            LOGGER.info("Result of POST request %s", result)

        return dri_value

    async def load_table(self, table: str) -> str:
        assert_type(table, str)
        await self.update_token()

        url = f"{self.api_url}/api/repos/dip.data.{table}/items"
        LOGGER.info("OYD LOAD TABLE url [ %s ]", url)
        async with ClientSession() as session:
            result = await session.get(
                url, headers={"Authorization": "Bearer " + self.token["access_token"]}
            )
            result = await unpack_response(result)
            LOGGER.info("OYD LOAD TABLE result: [ %s ]", result)

        return result
