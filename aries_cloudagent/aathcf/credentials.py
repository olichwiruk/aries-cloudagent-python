from aries_cloudagent.wallet.util import bytes_to_b64
from aries_cloudagent.messaging.util import time_now
from aries_cloudagent.messaging.valid import IndyISO8601DateTime
from marshmallow import fields, INCLUDE, Schema


def dictionary_to_base64(dictionary):
    dictionary_str = str(dictionary).encode("utf-8")
    dictionary_bytes = bytes(dictionary_str)
    dictionary_base64 = bytes_to_b64(dictionary_bytes).encode("utf-8")

    return dictionary_base64


async def verify_proof(wallet, credential: dict) -> bool:
    """
    Args: Credential: full schema with proof field
    """
    proof = credential["proof"]
    if proof["type"] != "Ed25519Signature2018":
        print("This proof type is not implemented, ", proof["type"])
        result = False

    del credential["proof"]
    proof_signature = bytes.fromhex(proof["jws"])
    credential_base64 = dictionary_to_base64(credential)

    result = await wallet.verify_message(
        credential_base64, proof_signature, proof["verificationMethod"]
    )

    return result


async def create_proof(wallet, credential: dict) -> dict:
    """
    Creates a proof dict with signature for given dictionary
    """
    signing_key: KeyInfo = await wallet.create_signing_key()

    credential_base64 = dictionary_to_base64(credential)
    signature_bytes: bytes = await wallet.sign_message(
        credential_base64, signing_key.verkey
    )
    signature_hex = signature_bytes.hex()

    proof_dict = {
        "type": "Ed25519Signature2018",
        "created": time_now(),
        # If the cryptographic suite expects a proofPurpose property,
        # it is expected to exist and be a valid value, such as assertionMethod.
        #
        "proofPurpose": "assertionMethod",
        # @TODO: verification method should point to something
        # that lets you verify the data, reference to signing entity
        # @
        # The verificationMethod property specifies,
        # for example, the public key that can be used
        # to verify the digital signature
        # @
        # Dereferencing a public key URL reveals information
        # about the controller of the key,
        # which can be checked against the issuer of the credential.
        "verificationMethod": signing_key.verkey,
        "jws": signature_hex,
    }

    return proof_dict


class ProofSchema(Schema):
    type = fields.Str(required=True)
    created = fields.Str(required=True, validate=IndyISO8601DateTime())
    proofPurpose = fields.Str(required=True)
    verificationMethod = fields.Str(required=True)
    jws = fields.Str(required=True)


class PresentationSchema(Schema):
    id = fields.Str(required=False)
    type = fields.List(fields.Str(required=True))
    proof = fields.List(fields.Nested(ProofSchema()), required=True)
    verifiableCredential = fields.List(fields.Dict(required=True), required=True)
    context = fields.List(fields.Str(required=True), required=True)


class CredentialSubjectSchema(Schema):
    """
    credentialSubject = fields.Nested(
        CredentialSubjectSchema(unknown=INCLUDE), required=True
    )
    Unknown INCLUDE so that unknown fields don't throw errors and
    are included
    """

    id = fields.Str(required=True)


class CredentialSchema(Schema):
    id = fields.Str(required=False)
    issuer = fields.Str(required=True)
    context = fields.List(fields.Str(required=True), required=True)
    type = fields.List(fields.Str(required=True), required=True)
    credentialSubject = fields.Nested(
        CredentialSubjectSchema(unknown=INCLUDE), required=True
    )
    proof = fields.Nested(ProofSchema(), required=True)
    issuanceDate = fields.Str(required=True)


class RequestedAttributesSchema(Schema):
    restrictions = fields.List(fields.Dict())


class PresentationRequestSchema(Schema):
    context = fields.List(fields.Str(required=True), required=True)
    type = fields.List(fields.Str(required=True), required=True)
    nonce = fields.Str(required=True)
    # TODO When I add more of these attributes
    # remember to change requiered to False
    # preferably check if there is at least one attribute
    # from available types
    requested_attributes = fields.Dict(
        keys=fields.Str(),
        values=fields.Nested(RequestedAttributesSchema),
        required=True,
    )


class RequestedCredentialsSchema(Schema):
    # TODO When I add more of these attributes
    # remember to change requiered to False
    # preferably check if there is at least one attribute
    # from available types
    requested_attributes = requested_attributes = fields.Dict(
        keys=fields.Str(),
        values=fields.Dict(),
        required=True,
        many=True,
    )


class PresentationSchema(Schema):
    context = fields.List(fields.Str(), required=True)
    id = fields.Str(required=True)
    type = fields.List(fields.Str(), required=True)
    verifiableCredential = fields.List(fields.Nested(CredentialSchema), required=True)
    proof = fields.Dict()