from ..messaging.models.base_record import BaseRecord, BaseRecordSchema
from marshmallow import fields


class THCFCredential(BaseRecord):
    class Meta:
        schema_class = "THCFCredentialSchema"

    RECORD_TYPE = "thcf_credential"
    RECORD_ID_NAME = "record_id"

    def __init__(
        self,
        *,
        id: str = None,
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


def THCFcreate_credential_from_dict(credential: dict) -> THCFCredential:
    # NOTE(KKrzosa): Make sure fields are not None
    issuer = credential["issuer"] if credential["issuer"] else None
    proof = credential["proof"] if credential["proof"] else None
    type = credential["type"] if credential["type"] else None
    id = credential["id"] if credential["id"] else None

    context = None
    if credential["@context"]:
        context = credential["@context"]
    elif credential["context"]:
        context = credential["context"]

    subject = None
    if credential["credentialSubject"]:
        subject = credential["credentialSubject"]

    # NOTE(KKrzosa): Make sure fields are of correct type
    assert isinstance(issuer, str)
    assert isinstance(id, str)
    assert isinstance(proof, dict)
    assert isinstance(subject, dict)
    assert isinstance(context, list)
    assert isinstance(type, list)

    result = THCFCredential(
        credentialSubject=subject,
        context=context,
        issuer=issuer,
        proof=proof,
        type=type,
        id=id,
    )

    print("THCFcreate_credential_from_dict", result)

    return result
