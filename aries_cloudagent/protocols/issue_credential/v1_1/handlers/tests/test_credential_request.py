import pytest
from asynctest import (
    mock as async_mock,
    TestCase as AsyncTestCase,
)

from aries_cloudagent.messaging.request_context import RequestContext
from aries_cloudagent.messaging.responder import MockResponder
from aries_cloudagent.transport.inbound.receipt import MessageReceipt
from aries_cloudagent.protocols.issue_credential.v1_1.messages.credential_request import (
    CredentialRequest,
)
from aries_cloudagent.protocols.issue_credential.v1_1.handlers.credential_request import (
    CredentialRequestHandler,
)
from aries_cloudagent.storage.basic import BasicStorage
from aries_cloudagent.storage.base import BaseStorage
from aries_cloudagent.protocols.issue_credential.v1_1.models.credential_exchange import (
    CredentialExchangeRecord,
)


class TestCredentialOfferHandler(AsyncTestCase):
    async def test_is_saving_record(self):
        context = RequestContext()
        context.message_receipt = MessageReceipt()
        storage = BasicStorage()
        context.injector.bind_instance(BaseStorage, storage)
        context.message = CredentialRequest(
            credential={
                "credential_type": "TEST",
                "credential_values": {"test": "one", "value": "two"},
            }
        )
        context.connection_ready = True
        handler_inst = CredentialRequestHandler()
        responder = MockResponder()
        responder.connection_id = "1234"
        await handler_inst.handle(context, responder)

        assert len(responder.messages) == 0
        assert 1 == len(responder.webhooks)

        id = responder.webhooks[0][1]["credential_exchange_id"]
        exchange = await CredentialExchangeRecord.retrieve_by_id(context, id)
        assert exchange != None
        assert exchange.connection_id == responder.connection_id
        assert exchange.state == CredentialExchangeRecord.STATE_REQUEST_RECEIVED
        assert exchange.credential_request == context.message.credential
