from .base import BasePersonalDataStorage
from .api import encode
from .error import PersonalDataStorageError

import json
import logging
from urllib.parse import urlparse

from aiohttp import ClientSession
from aries_cloudagent.aathcf.credentials import assert_type
import time

LOGGER = logging.getLogger(__name__)


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
                    "Please configure the plugin, Client_id is empty"
                )
            if client_secret is None:
                raise PersonalDataStorageError(
                    "Please configure the plugin, Client_secret is empty"
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
                if result.status != 200:
                    raise PersonalDataStorageError(
                        "Server Error, Could be that the connection is invalid or some other unforseen error, check if the server is up"
                    )

                result = await result.text()
                token = json.loads(result)
                self.token = token
                self.token_timestamp = time.time()
                LOGGER.info("update token: %s", self.token)

            """
            Download the usage policy

            """

            async with ClientSession() as session:
                result = await session.get(
                    f"{self.api_url}/api/meta/usage",
                    headers={"Authorization": "Bearer " + self.token["access_token"]},
                )

                self.settings["usage_policy"] = await result.text()
                LOGGER.info("Usage policy %s", self.settings["usage_policy"])

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
            result_str: str = await result.text()

            """

            Strip the {"content": ""}

            """

            beginning_to_delete = '{"content":"'
            to_delete_size = len(beginning_to_delete)
            # -2 cause it has to end with "}
            if result_str[0:to_delete_size] == '{"content":"':
                result_str = result_str[to_delete_size:-2]

            LOGGER.info("Result of GET request %s", result_str)

        return result_str

    async def save(self, record: str, metadata: str) -> str:
        """
        meta: {
            "table" - specifies the table name into which save the data
            "oca_schema_dri"
        }
        """

        table = self.settings.get("repo")
        table = table if table is not None else "dip.data"
        dri_value = encode(record)
        meta = json.loads(metadata)

        await self.update_token()
        LOGGER.info("OYD save record %s metadata %s", record, meta)
        async with ClientSession() as session:
            """
            Pack request body
            """

            if meta.get("table") is not None:
                table = f"{table}.{meta.get('table')}"

            body = {
                "content": json.loads(record),
                "dri": dri_value,
                "table_name": table,
                "mime_type": "application/json",
            }

            if meta.get("oca_schema_dri") is not None:
                body["schema_dri"] = meta["oca_schema_dri"]

            print(body)
            print(self.token)

            """
            Request
            """

            response = await session.post(
                f"{self.api_url}/api/data",
                headers={"Authorization": "Bearer " + self.token["access_token"]},
                json=body,
            )
            result = await response.text()
            print("Result POST DATA TO OYD", result)
            assert response.status == 200, "Request failed, != 200"
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
            result = await result.text()
            LOGGER.info("OYD LOAD TABLE result: [ %s ]", result)

        return result
