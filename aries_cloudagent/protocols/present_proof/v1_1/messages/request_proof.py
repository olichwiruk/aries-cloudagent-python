from typing import Sequence

from marshmallow import fields

from .....messaging.agent_message import AgentMessage, AgentMessageSchema
from ..message_types import REQUEST_PROOF, PROTOCOL_PACKAGE
from aries_cloudagent.aathcf.credentials import RequestedAttributesSchema
import uuid

HANDLER_CLASS = f"{PROTOCOL_PACKAGE}.handlers.request_proof.RequestProofHandler"


class RequestProof(AgentMessage):
    class Meta:
        handler_class = HANDLER_CLASS
        schema_class = "RequestProofSchema"
        message_type = REQUEST_PROOF

    def __init__(
        self,
        _id: str = None,
        *,
        requested_attributes: dict = {},
        context: list = [],
        type: list = [],
        nonce: str = None,
        **kwargs,
    ):
        """Initialize credential issue object."""
        super().__init__(_id=_id, **kwargs)
        self.type = type
        self.context = (context,)
        self.nonce = str(uuid.uuid4()) if nonce == None else nonce
        self.requested_attributes = requested_attributes


class RequestProofSchema(AgentMessageSchema):
    """Credential schema."""

    class Meta:
        """Credential schema metadata."""

        model_class = RequestProof

    requested_attributes = fields.Dict(
        keys=fields.Str(),
        values=fields.Nested(RequestedAttributesSchema),
        required=True,
        many=True,
    )
    context = fields.List(fields.Str(required=True), required=True)
    type = fields.List(fields.Str(required=True), required=True)
    nonce = fields.Str(required=True)