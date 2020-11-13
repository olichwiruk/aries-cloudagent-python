from .....messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    HandlerException,
    RequestContext,
)
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
from aries_cloudagent.protocols.present_proof.v1_1.messages.present_proof import (
    PresentProof,
)


# TODO Error handling
class PresentProofHandler(BaseHandler):
    """
    Message handler logic for incoming credential requests.
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        debug_handler(self._logger.info, context, PresentProof)
        message: PresentProof = context.message
        self._logger.info("Message serialized %s", message.serialize())

        await responder.send_webhook(
            "present_proof",
            {
                "type": "request_proof",
                "exchange_record_id": message.serialize(),
                "connection_id": responder.connection_id,
            },
        )