from .....messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    HandlerException,
    RequestContext,
)
from ..messages.request_proof import RequestProof
from aries_cloudagent.holder.base import BaseHolder, HolderError
from aries_cloudagent.issuer.base import BaseIssuer, IssuerError
from aries_cloudagent.connections.models.connection_record import ConnectionRecord
import json
from aries_cloudagent.protocols.issue_credential.v1_1.models.credential_exchange import (
    CredentialExchangeRecord,
)
from ....issue_credential.v1_1.handlers.utils import debug_handler
from aries_cloudagent.protocols.present_proof.v1_1.models.presentation_exchange import (
    THCFPresentationExchange,
)


# TODO Error handling
class RequestProofHandler(BaseHandler):
    """
    Message handler logic for incoming credential requests.
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        debug_handler(self._logger.info, context, RequestProof)
        message: RequestProof = context.message
        exchange_record = THCFPresentationExchange(
            connection_id=responder.connection_id,
            thread_id=message._thread_id,
            initiator=THCFPresentationExchange.INITIATOR_EXTERNAL,
            role=THCFPresentationExchange.ROLE_PROVER,
            state=THCFPresentationExchange.STATE_REQUEST_RECEIVED,
            presentation_request=message.presentation_request,
        )
        record_id = await exchange_record.save(context)

        await responder.send_webhook(
            "present_proof",
            {
                "type": "request_proof",
                "exchange_record_id": record_id,
                "connection_id": responder.connection_id,
            },
        )