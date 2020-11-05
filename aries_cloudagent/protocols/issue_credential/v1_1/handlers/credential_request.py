from .....messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    HandlerException,
    RequestContext,
)
from ..messages.credential_issue import CredentialIssue
from ..messages.credential_request import CredentialRequest
from aries_cloudagent.holder.base import BaseHolder, HolderError
from aries_cloudagent.issuer.base import BaseIssuer, IssuerError
from aries_cloudagent.connections.models.connection_record import ConnectionRecord
import json
from aries_cloudagent.protocols.issue_credential.v1_1.models.credential_exchange import (
    CredentialExchangeRecord,
)
from .utils import debug_handler


# TODO Error handling
class CredentialRequestHandler(BaseHandler):
    """
    Message handler logic for incoming credential requests.
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        debug_handler(
            self._logger.debug, context, CredentialRequest, "CredentialRequestHandler"
        )
        message: CredentialRequest = context.message
        credential = context.message.credential
        credential_type = credential.get("credential_type")
        credential_values = credential.get("credential_values")

        assert message._thread_id != None
        exchange_record: CredentialExchangeRecord = CredentialExchangeRecord(
            connection_id=responder.connection_id,
            initiator=CredentialExchangeRecord.INITIATOR_EXTERNAL,
            role=CredentialExchangeRecord.ROLE_ISSUER,
            state=CredentialExchangeRecord.STATE_REQUEST_RECEIVED,
            thread_id=message._thread_id,
            credential_request=credential,
        )

        credential_exchange_id: CredentialExchangeRecord = await exchange_record.save(
            context, reason="RequestCredential ExchangeRecord saved"
        )

        self._logger.info("Credential exchange ID %s", credential_exchange_id)
        await responder.send_webhook(
            "TODOInfo_credential_request_received",
            {
                "credential_exchange_id": credential_exchange_id,
                "connection_id": responder.connection_id,
            },
        )
        # auto_issue = True
        # if auto_issue:
        #     issuer: BaseIssuer = await context.inject(BaseIssuer)
        #     credential, _ = await issuer.create_credential(
        #         schema={
        #             "credential_type": credential_type,
        #         },
        #         credential_values=credential_values,
        #         credential_offer={},
        #         credential_request={
        #             "connection_record": context.connection_record,
        #         },
        #     )

        #     issue = CredentialIssue(credential=json.loads(credential))
        #     await responder.send_reply(message=issue)

        # await responder.send_webhook(
        #     "TODOInfo_credential_request_received",
        #     {"credential": credential, "connection_id": responder.connection_id},
        # )