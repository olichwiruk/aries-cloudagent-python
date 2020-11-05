from .....messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    HandlerException,
    RequestContext,
)
from ..messages.credential_issue import CredentialIssue
from aries_cloudagent.holder.base import BaseHolder, HolderError
from .utils import debug_handler
from aries_cloudagent.protocols.issue_credential.v1_1.models.credential_exchange import (
    CredentialExchangeRecord,
)
from aries_cloudagent.storage.error import StorageNotFoundError


class CredentialIssueHandler(BaseHandler):
    """
    Message handler logic for incoming credential issues.
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        debug_handler(
            self._logger.debug, context, CredentialIssue, "CredentialIssueHandler"
        )

        try:
            exchange_record: CredentialExchangeRecord = (
                await CredentialExchangeRecord.retrieve_by_connection_and_thread(
                    context, responder.connection_id, context.message._thread_id
                )
            )
        except StorageNotFoundError:
            raise HandlerException(
                """Couldn't retrieve ExchangeRecord for this CredentialIssue 
                as a result, credential issue was not handled"""
            )

        # TODO: Check Credential request equal to credential
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
            raise HandlerException(
                "Error on store_credential async! TODO Error handling ", err.roll_up
            )

        self._logger.info("Stored Credential ID %s", credential_id)
        await responder.send_webhook(
            "TODOInfocredential_issue_received",
            {"credential_id": credential_id, "connection_id": responder.connection_id},
        )