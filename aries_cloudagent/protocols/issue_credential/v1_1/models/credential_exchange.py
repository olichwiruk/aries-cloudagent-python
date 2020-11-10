"""Aries#0036 v1.0 credential exchange information with non-secrets storage."""

from typing import Any

from marshmallow import fields, validate

from .....config.injection_context import InjectionContext
from .....messaging.models.base_record import BaseExchangeRecord, BaseExchangeSchema
from .....messaging.valid import UUIDFour


class CredentialExchangeRecord(BaseExchangeRecord):
    """Represents an credential exchange."""

    class Meta:
        """CredentialExchange metadata."""

        schema_class = "CredentialExchangeSchema"

    RECORD_TYPE = "credential_exchange_"
    RECORD_ID_NAME = "credential_exchange_id"
    WEBHOOK_TOPIC = "issue_credential"
    TAG_NAMES = {"thread_id"}

    INITIATOR_SELF = "self"
    INITIATOR_EXTERNAL = "external"
    ROLE_ISSUER = "issuer"
    ROLE_HOLDER = "holder"

    STATE_PROPOSAL_SENT = "proposal_sent"
    STATE_PROPOSAL_RECEIVED = "proposal_received"
    STATE_OFFER_SENT = "offer_sent"
    STATE_OFFER_RECEIVED = "offer_received"
    STATE_REQUEST_SENT = "request_sent"
    STATE_REQUEST_RECEIVED = "request_received"
    STATE_ISSUED = "credential_issued"
    STATE_CREDENTIAL_RECEIVED = "credential_received"
    STATE_ACKED = "credential_acked"

    def __init__(
        self,
        *,
        connection_id: str = None,
        initiator: str = None,
        role: str = None,
        state: str = None,
        thread_id: str = None,
        trace: bool = False,
        credential_request: dict = None,
        credential_id: str = None,
        credential_exchange_id: str = None,
        **kwargs,
    ):
        """
        Init.

        thread_id - for now assumption is that we want the same thread id
        for entire exchange between agents, all messages in exchange should have same
        id.
        """
        super().__init__(credential_exchange_id, state, trace=trace, **kwargs)
        self._id = credential_exchange_id
        self.connection_id = connection_id
        self.thread_id = thread_id
        self.initiator = initiator
        self.role = role
        self.state = state
        self.trace = trace
        self.credential_request = credential_request
        self.credential_id = credential_id

    @property
    def credential_exchange_id(self) -> str:
        """Accessor for the ID associated with this exchange."""
        return self._id

    @property
    def record_value(self) -> dict:
        """Accessor for the JSON record value generated for this credential exchange."""
        return {
            prop: getattr(self, prop)
            for prop in (
                "connection_id",
                "credential_id",
                "thread_id",
                "credential_request",
                "initiator",
                "role",
                "state",
                "trace",
            )
        }

    @property
    def record_tags(self) -> dict:
        """Used to define tags with which record can be found."""
        return {
            prop: getattr(self, prop)
            for prop in (
                "connection_id",
                "thread_id",
                "initiator",
                "role",
                "state",
            )
        }

    @classmethod
    async def retrieve_by_connection_and_thread(
        cls, context: InjectionContext, connection_id: str, thread_id: str
    ):
        """Retrieve a credential exchange record by connection and thread ID."""
        cache_key = f"credential_exchange_ctidx::{connection_id}::{thread_id}"
        record_id = await cls.get_cached_key(context, cache_key)
        if record_id:
            record = await cls.retrieve_by_id(context, record_id)
        else:
            record = await cls.retrieve_by_tag_filter(
                context,
                {"thread_id": thread_id},
                {"connection_id": connection_id} if connection_id else None,
            )
            await cls.set_cached_key(context, cache_key, record.credential_exchange_id)
        return record

    def __eq__(self, other: Any) -> bool:
        """Comparison between records."""
        return super().__eq__(other)


class CredentialExchangeSchema(BaseExchangeSchema):
    """Schema to allow serialization/deserialization of credential exchange records."""

    class Meta:
        """CredentialExchangeSchema metadata."""

        model_class = CredentialExchangeRecord

    credential_exchange_id = fields.Str(
        required=False,
        description="Credential exchange identifier",
        example=UUIDFour.EXAMPLE,
    )
    connection_id = fields.Str(
        required=False, description="Connection identifier", example=UUIDFour.EXAMPLE
    )
    thread_id = fields.Str(
        required=False, description="Thread identifier", example=UUIDFour.EXAMPLE
    )
    credential_id = fields.Str(
        required=False, description="Credential identifier", example=UUIDFour.EXAMPLE
    )
    initiator = fields.Str(
        required=False,
        description="Issue-credential exchange initiator: self or external",
        example=CredentialExchangeRecord.INITIATOR_SELF,
        validate=validate.OneOf(["self", "external"]),
    )
    role = fields.Str(
        required=False,
        description="Issue-credential exchange role: holder or issuer",
        example=CredentialExchangeRecord.ROLE_ISSUER,
        validate=validate.OneOf(["holder", "issuer"]),
    )
    state = fields.Str(
        required=False,
        description="Issue-credential exchange state",
        example=CredentialExchangeRecord.STATE_ACKED,
    )
    credential_request = fields.Dict(required=False, description="")
