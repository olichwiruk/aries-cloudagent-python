from .....messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    HandlerException,
    RequestContext,
)
from ....issue_credential.v1_1.handlers.utils import debug_handler
from aries_cloudagent.protocols.present_proof.v1_1.models.presentation_exchange import (
    THCFPresentationExchange,
)
from aries_cloudagent.protocols.present_proof.v1_1.messages.present_proof import (
    PresentProof,
)
from aries_cloudagent.verifier.base import BaseVerifier
from ..models.utils import retrieve_exchange_by_thread, validate_exchange_state


# TODO Error handling
class PresentProofHandler(BaseHandler):
    """
    Message handler logic for incoming credential presentations / incoming proofs.
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        debug_handler(self._logger.info, context, PresentProof)
        verifier: BaseVerifier = await context.inject(BaseVerifier)
        presentation = context.message.credential_presentation

        assert context.message._thread_id != None
        exchange_record: THCFPresentationExchange = await retrieve_exchange_by_thread(
            context,
            responder.connection_id,
            context.message._thread_id,
            HandlerException,
        )

        if exchange_record.state != THCFPresentationExchange.STATE_REQUEST_SENT:
            raise HandlerException(
                f"""Invalid exchange state, should be {THCFPresentationExchange.STATE_REQUEST_SENT}
        currently is {exchange_record.state}"""
            )
        if exchange_record.role != THCFPresentationExchange.ROLE_VERIFIER:
            raise HandlerException(
                f"""Invalid exchange role, should be {THCFPresentationExchange.ROLE_VERIFIER}
        currently is {exchange_record.role}"""
            )

        if (
            await verifier.verify_presentation(
                exchange_record.presentation_request, presentation, {}, {}, {}, {}
            )
            == False
        ):
            raise HandlerException("Verifier couldn't verify the presentation!")

        exchange_record.presentation = presentation
        exchange_record.verified = True
        exchange_record.state = exchange_record.STATE_VERIFIED
        await exchange_record.save(context, "PresentationExchange updated!")

        await responder.send_webhook(
            "present_proof",
            {
                "type": "present_proof",
                "exchange_record_id": exchange_record._id,
                "connection_id": responder.connection_id,
            },
        )