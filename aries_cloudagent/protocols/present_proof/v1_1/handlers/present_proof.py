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
from aries_cloudagent.protocols.present_proof.v1_1.messages.present_proof import (
    PresentProof,
)
from aries_cloudagent.verifier.base import BaseVerifier
from ..models.utils import retrieve_exchange_by_thread
import json
from collections import OrderedDict
from aries_cloudagent.aathcf.credentials import raise_exception_invalid_state


# TODO Error handling
class PresentProofHandler(BaseHandler):
    """
    Message handler logic for incoming credential presentations / incoming proofs.
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        debug_handler(self._logger.info, context, PresentProof)
        verifier: BaseVerifier = await context.inject(BaseVerifier)

        presentation = json.loads(
            context.message.credential_presentation, object_pairs_hook=OrderedDict
        )

        exchange_record: THCFPresentationExchange = await retrieve_exchange_by_thread(
            context,
            responder.connection_id,
            context.message._thread_id,
            HandlerException,
        )

        raise_exception_invalid_state(
            exchange_record,
            THCFPresentationExchange.STATE_REQUEST_SENT,
            THCFPresentationExchange.ROLE_VERIFIER,
            HandlerException,
        )

        is_verified = await verifier.verify_presentation(
            presentation_request=exchange_record.presentation_request,
            presentation=presentation,
            schemas={},
            credential_definitions={},
            rev_reg_defs={},
            rev_reg_entries={},
        )

        if not is_verified:
            raise HandlerException(
                f"Verifier couldn't verify the presentation! {is_verified}"
            )

        exchange_record.presentation = presentation
        exchange_record.verified = True
        exchange_record.prover_public_did = context.message.prover_public_did
        exchange_record.state = exchange_record.STATE_PRESENTATION_RECEIVED
        await exchange_record.save(context, reason="PresentationExchange updated!")

        await responder.send_webhook(
            "present_proof",
            {
                "type": "present_proof",
                "exchange_record_id": exchange_record._id,
                "connection_id": responder.connection_id,
            },
        )
