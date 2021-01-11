from .....messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    HandlerException,
    RequestContext,
)
from ..messages.credential_issue import CredentialIssue
from aries_cloudagent.holder.base import BaseHolder, HolderError
from aries_cloudagent.aathcf.utils import debug_handler
from aries_cloudagent.protocols.issue_credential.v1_1.models.credential_exchange import (
    CredentialExchangeRecord,
)
from aries_cloudagent.storage.error import StorageError, StorageNotFoundError
import json
from collections import OrderedDict


class CredentialIssueHandler(BaseHandler):
    """
    Message handler logic for incoming credential issues.
    Verifies and saves the issued credential received from issuer.
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        debug_handler(self._logger.debug, context, CredentialIssue)

        try:
            exchange: CredentialExchangeRecord = (
                await CredentialExchangeRecord.retrieve_by_connection_and_thread(
                    context, responder.connection_id, context.message._thread_id
                )
            )
        except StorageNotFoundError:
            raise HandlerException(
                "Couldn't retrieve ExchangeRecord for this CredentialIssue"
                "as a result, credential issue was not handled"
            )
        except StorageError as err:
            raise HandlerException(err.roll_up)

        if exchange.role != exchange.ROLE_HOLDER:
            raise HandlerException(reason="Invalid exchange role")
        if exchange.state != exchange.STATE_REQUEST_SENT:
            raise HandlerException(reason="Invalid exchange state")

        credential_message = context.message
        requested_credential = exchange.credential_request
        issued_credential = json.loads(
            credential_message.credential, object_pairs_hook=OrderedDict
        )

        for key in requested_credential.get("credential_values"):
            if issued_credential.get("credentialSubject").get(
                key
            ) != requested_credential.get("credential_values").get(key):
                raise HandlerException(
                    f"Requested Credential VALUES differ from Issued Credential"
                    f"RequestedCredential: {requested_credential}"
                    f"IssuedCredential: {issued_credential}"
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

        exchange.state = exchange.STATE_CREDENTIAL_RECEIVED
        exchange.credential_id = credential_id

        self._logger.info("Stored Credential ID %s", credential_id)
        await responder.send_webhook(
            "issue-credential/credential-received",
            {"credential_id": credential_id, "connection_id": responder.connection_id},
        )
