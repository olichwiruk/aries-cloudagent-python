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


# TODO Error handling
class RequestProofHandler(BaseHandler):
    """
    Message handler logic for incoming credential requests.
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        debug_handler(self._logger.info, context, RequestProof)
        self._logger.info("IT WORKS")

        # await responder.send_webhook(
        #     "TODOInfo_credential_request_received",
        #     {
        #         "credential_exchange_id": credential_exchange_id,
        #         "connection_id": responder.connection_id,
        #     },
        # )