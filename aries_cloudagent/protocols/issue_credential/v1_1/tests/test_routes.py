from asynctest import TestCase as AsyncTestCase
from asynctest import mock as async_mock

from aiohttp import web as aio_web

from .....config.injection_context import InjectionContext
from .....holder.base import BaseHolder
from .....messaging.request_context import RequestContext
from .....wallet.base import DIDInfo

from .. import routes as test_module
from aries_cloudagent.storage.base import BaseStorage
from aries_cloudagent.storage.basic import BasicStorage
from aries_cloudagent.connections.models.connection_record import ConnectionRecord


class TestCredentialRoutes(AsyncTestCase):
    async def test_request_credential(self):
        mock = async_mock.MagicMock()
        record = ConnectionRecord(state=ConnectionRecord.STATE_ACTIVE)
        context = RequestContext(base_context=InjectionContext(enforce_typing=False))
        storage = BasicStorage()
        context.injector.bind_instance(BaseStorage, storage)
        connection_id = await record.save(context)
        mock.json = async_mock.CoroutineMock(
            return_value={
                "connection_id": connection_id,
                "credential_type": "TYPE_EXAMPLE",
                "credential_values": {"test1": "1"},
            }
        )

        mock.app = {
            "request_context": context,
            "outbound_message_router": async_mock.CoroutineMock(),
        }

        with async_mock.patch.object(
            test_module, "CredentialExchangeRecord", autospec=True
        ) as mock_conn_rec, async_mock.patch.object(
            test_module.web, "json_response"
        ) as mock_response:

            await test_module.request_credential(mock)
            mock_response.assert_called_once()
