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
from aries_cloudagent.aathcf.utils import debug_handler


class CredentialRequestHandler(BaseHandler):
    """
    Message handler logic for incoming credential requests.
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        debug_handler(self._logger.debug, context, CredentialRequest)
        message: CredentialRequest = context.message
        credential = context.message.credential

        exchange_record: CredentialExchangeRecord = CredentialExchangeRecord(
            connection_id=responder.connection_id,
            initiator=CredentialExchangeRecord.INITIATOR_EXTERNAL,
            role=CredentialExchangeRecord.ROLE_ISSUER,
            state=CredentialExchangeRecord.STATE_REQUEST_RECEIVED,
            thread_id=message._thread_id,
            credential_request=credential,
        )

        credential_exchange_id = await exchange_record.save(context)
        await responder.send_webhook(
            CredentialExchangeRecord.webhook_topic,
            {
                "credential_exchange_id": credential_exchange_id,
                "connection_id": responder.connection_id,
            },
        )
