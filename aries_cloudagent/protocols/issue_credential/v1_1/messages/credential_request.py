from typing import Sequence

from marshmallow import fields

from .....messaging.agent_message import AgentMessage, AgentMessageSchema
from ..message_types import CREDENTIAL_REQUEST, PROTOCOL_PACKAGE

HANDLER_CLASS = (
    f"{PROTOCOL_PACKAGE}.handlers.credential_request.CredentialRequestHandler"
)


class CredentialRequest(AgentMessage):
    class Meta:
        handler_class = HANDLER_CLASS
        schema_class = "CredentialRequestSchema"
        message_type = CREDENTIAL_REQUEST

    def __init__(
        self,
        _id: str = None,
        *,
        credential: dict = None,
        **kwargs,
    ):
        """Initialize credential issue object."""
        super().__init__(_id=_id, **kwargs)
        # TODO; Schema
        self.credential = credential


class CredentialRequestSchema(AgentMessageSchema):
    """Credential schema."""

    class Meta:
        """Credential schema metadata."""

        model_class = CredentialRequest

    credential = fields.Dict()