from marshmallow import fields
from .....messaging.agent_message import AgentMessage, AgentMessageSchema
from ..message_types import ACKNOWLEDGE_PROOF, PROTOCOL_PACKAGE

HANDLER_CLASS = f"{PROTOCOL_PACKAGE}.handlers.acknowledge_proof.AcknowledgeProofHandler"


class AcknowledgeProof(AgentMessage):
    class Meta:
        handler_class = HANDLER_CLASS
        schema_class = "AcknowledgeProofSchema"
        message_type = ACKNOWLEDGE_PROOF

    def __init__(
        self,
        _id: str = None,
        *,
        credential=None,
        **kwargs,
    ):
        """Initialize credential issue object."""
        super().__init__(_id=_id, **kwargs)
        self.credential = credential


class AcknowledgeProofSchema(AgentMessageSchema):
    """Credential schema."""

    class Meta:
        """Credential schema metadata."""

        model_class = AcknowledgeProof

    credential = fields.Str(required=False)
