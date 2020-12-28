from .....messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    HandlerException,
    RequestContext,
)
from aries_cloudagent.aathcf.utils import debug_handler
from aries_cloudagent.protocols.present_proof.v1_1.models.presentation_exchange import (
    THCFPresentationExchange,
)
from aries_cloudagent.protocols.present_proof.v1_1.messages.acknowledge_proof import (
    AcknowledgeProof,
)
from aries_cloudagent.verifier.base import BaseVerifier
from ..models.utils import retrieve_exchange_by_thread
import json
from collections import OrderedDict
from aries_cloudagent.aathcf.credentials import raise_exception_invalid_state


# TODO Error handling
class AcknowledgeProofHandler(BaseHandler):
    """
    Message handler logic for incoming credential presentations / incoming proofs.
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        debug_handler(self._logger.info, context, AcknowledgeProof)

        exchange_record: THCFPresentationExchange = await retrieve_exchange_by_thread(
            context,
            responder.connection_id,
            context.message._thread_id,
            HandlerException,
        )

        raise_exception_invalid_state(
            exchange_record,
            THCFPresentationExchange.STATE_PRESENTATION_SENT,
            THCFPresentationExchange.ROLE_PROVER,
            HandlerException,
        )

        exchange_record.acknowledgment_credential = context.message.credential
        exchange_record.state = exchange_record.STATE_ACKNOWLEDGED
        await exchange_record.save(context)

        await responder.send_webhook(
            "present_proof",
            {
                "type": "acknowledge_proof",
                "exchange_record_id": exchange_record._id,
                "connection_id": responder.connection_id,
            },
        )
