from ...messaging.models.base_record import BaseRecord, BaseRecordSchema
from marshmallow import fields


class THCFCredential(BaseRecord):
    class Meta:
        schema_class = "THCFCredentialSchema"

    RECORD_TYPE = "thcf_credential"
    RECORD_ID_NAME = "record_id"

    def __init__(
        self,
        *,
        id: str = None,  # pointer to a machine_readable document
        credentialSubject: dict = None,
        context: list = None,
        type: list = None,
        issuer: str = None,
        proof: dict = None,
        record_id: str = None,
        **kwargs
    ):
        super().__init__(record_id, None, **kwargs)
        self.credentialSubject = credentialSubject
        self.id = id
        self.context = context
        self.type = type
        self.issuer = issuer
        self.proof = proof

    @property
    def record_value(self) -> dict:
        return {
            prop: getattr(self, prop)
            for prop in (
                "id",
                "type",
                "proof",
                "issuer",
                "context",
                "credentialSubject",
            )
        }


class THCFCredentialSchema(BaseRecordSchema):
    class Meta:
        model_class = "THCFCredential"

    id = fields.Str(required=False)
    issuer = fields.Str(required=False)
    context = fields.List(fields.Str(), required=False)
    type = fields.List(fields.Str(), required=False)
    credentialSubject = fields.Dict(required=False)
    proof = fields.Dict(required=False)
