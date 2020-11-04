from .....messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    HandlerException,
    RequestContext,
)
from ..messages.credential_issue import CredentialIssue
from ..messages.credential_request import CredentialRequest
from aries_cloudagent.holder.base import BaseHolder, HolderError
from aries_cloudagent.issuer.base import BaseIssuer, IssuerError
from aries_cloudagent.connections.models.connection_record import ConnectionRecord

# TODO Error handling
class CredentialRequestHandler(BaseHandler):
    """
    Message handler logic for incoming credential issues.
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        self._logger.debug("CredentialHandler called with context %s", context)
        assert isinstance(context.message, CredentialRequest)
        self._logger.info(
            "Received credential message: %s", context.message.serialize(as_string=True)
        )

        if not context.connection_ready:
            raise HandlerException("No connection established for credential request")

        connection: ConnectionRecord = await ConnectionRecord.retrieve_by_id(
            context, responder.connection_id
        )
        credential_message: CredentialRequest = context.message
        credential = credential_message.credential

        cred_type = credential.get("credential_type")
        cred_values = credential.get("credential_values")

        auto_issue = True
        if auto_issue:
            issuer: BaseIssuer = await context.inject(BaseIssuer)
            credential, _ = await issuer.create_credential(
                schema={
                    "credential_type": cred_type,
                },
                credential_values=cred_values,
                credential_offer={},
                credential_request={
                    "connection_record": connection,
                },
            )

            issue = CredentialIssue(credential=credential)
            await responder.send_reply(message=issue)

        await responder.send_webhook(
            "TODOInfo_credential_request_received",
            {"credential": credential, "connection_id": responder.connection_id},
        )