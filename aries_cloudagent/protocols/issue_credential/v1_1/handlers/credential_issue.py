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
from aries_cloudagent.storage.error import StorageError, StorageNotFoundError


class CredentialIssueHandler(BaseHandler):
    """
    Message handler logic for incoming credential issues.
    Verifies and saves the issued credential received from issuer.
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        debug_handler(self._logger.debug, context, CredentialIssue)

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
        except StorageError as err:
            raise HandlerException(err.roll_up)

        credential_message: CredentialIssue = context.message
        requested_credential = exchange_record.credential_request
        issued_credential = credential_message.credential

        if requested_credential["credential_type"] not in issued_credential["type"]:
            raise HandlerException(
                f"""Requested Credential TYPE differs from Issued Credential,
                RequestedCredential: {requested_credential},
                IssuedCredential: {issued_credential}"""
            )

        for key in requested_credential["credential_values"]:
            if (
                issued_credential["credentialSubject"][key]
                != requested_credential["credential_values"][key]
            ):
                raise HandlerException(
                    f"""Requested Credential VALUES differ from Issued Credential,
                    RequestedCredential: {requested_credential},
                    IssuedCredential: {issued_credential}"""
                )

        holder: BaseHolder = await context.inject(BaseHolder)
        try:
            credential_id = await holder.store_credential(
                credential_definition={},
                credential_data=issued_credential,
                credential_request_metadata={},
            )
        except HolderError as err:
            # TODO Problem report
            raise HandlerException(
                "Error on store_credential async! TODO Error handling", err.roll_up
            )

        exchange_record.state = exchange_record.STATE_ISSUED
        exchange_record.credential_id = credential_id

        self._logger.info("Stored Credential ID %s", credential_id)
        await responder.send_webhook(
            "TODOInfocredential_issue_received",
            {"credential_id": credential_id, "connection_id": responder.connection_id},
        )