from .....messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    HandlerException,
    RequestContext,
)
from ..messages.credential_issue import CredentialIssue
from aries_cloudagent.holder.base import BaseHolder, HolderError


class CredentialIssueHandler(BaseHandler):
    """
    Message handler logic for incoming credential issues.
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        self._logger.debug("CredentialHandler called with context %s", context)
        assert isinstance(context.message, CredentialIssue)
        self._logger.info(
            "Received credential message: %s", context.message.serialize(as_string=True)
        )

        if not context.connection_ready:
            raise HandlerException("No connection established for credential request")

        credential_message: CredentialIssue = context.message
        credential = credential_message.credential

        holder: BaseHolder = await context.inject(BaseHolder)
        try:
            credential_id = await holder.store_credential(
                credential_definition={},
                credential_data=credential,
                credential_request_metadata={},
            )
        except HolderError as err:
            # TODO Problem report
            credential_id = err.roll_up
            self._logger.error(
                "Error on store_credential async! TODO Error handling %s", err.roll_up
            )

        await responder.send_webhook(
            "TODOInfocredential_issue_received",
            {"credential_id": credential_id, "connection_id": responder.connection_id},
        )