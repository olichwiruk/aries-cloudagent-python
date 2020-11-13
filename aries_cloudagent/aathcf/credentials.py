from aries_cloudagent.wallet.util import bytes_to_b64, str_to_b64
from aries_cloudagent.messaging.util import time_now
from aries_cloudagent.messaging.valid import IndyISO8601DateTime
from marshmallow import fields, INCLUDE, Schema

import json


def dictionary_to_base64(dictionary):
    dictionary_str = str(dictionary).encode("utf-8")
    dictionary_bytes = bytes(dictionary_str)
    dictionary_base64 = bytes_to_b64(dictionary_bytes).encode("utf-8")

    return dictionary_base64


async def verify_proof(wallet, credential: dict) -> bool:
    """
    Args: Credential: full schema with proof field
    """
    cred_copy = credential.copy()
    proof = cred_copy["proof"]
    if proof["type"] != "Ed25519Signature2018":
        print("This proof type is not implemented, ", proof["type"])
        result = False

    del cred_copy["proof"]
    proof_signature = bytes.fromhex(proof["jws"])
    credential_base64 = dictionary_to_base64(cred_copy)

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
        many=True,
    )


class RequestedCredentialsSchema(Schema):
    """
    Schema which is used to provide credential_ids for credential_request
    """

    # TODO When I add more of these attributes
    # remember to change requiered to False
    # preferably check if there is at least one attribute
    # from available types
    requested_attributes = fields.Dict(
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
    created_at = fields.Date(required=False)
    updated_at = fields.Date(required=False)


## TODO:
async def create_proof_jwt(wallet, credential):
    def dictionary_to_base64_jwt(dictionary) -> bytes:
        dictionary_str = json.dumps(dictionary)
        dictionary_base64 = str_to_b64(dictionary_str, urlsafe=True).encode("utf-8")

        return dictionary_base64

    """
    JWT:
    https://tools.ietf.org/html/rfc7519
    JWS:
    https://tools.ietf.org/html/rfc7515
    """
    signing_key: KeyInfo = await wallet.create_signing_key()
    header = {"alg": "EdDSA", "typ": "JWT"}
    payload_fields = {
        "iss": "",  # issuer
        "aud": "",  # audience
        "sub": "",  # subject
        "iat": time_now(),  # Issued At epoch
        "exp": time_now(),  # expiration epoch
    }
    payload_fields.update(credential)

    test_2 = {"iss": "joe", "exp": 1300819380, "http://example.com/is_root": True}
    test = {"typ": "JWT", "alg": "HS256"}
    test_abc = dictionary_to_base64_jwt(test_2)
    return test_abc

    """
        * The "iss" value is a case-sensitive string containing a StringOrURI
        value.  Use of this claim is OPTIONAL
        * sub - who jwt is about, subject
        * aud - audience, receiver of jwt 
        * The "nbf" (not before) claim identifies the time before which the JWT
        MUST NOT be accepted for processing.
        * The "jti" (JWT ID) claim provides a unique identifier for the JWT.
        The identifier value MUST be assigned in a manner that ensures that
        there is a negligible probability that the same value will be
        accidentally assigned to a different data object
    """

    header_base64: bytes = dictionary_to_base64_jwt(header)
    payload_base64: bytes = dictionary_to_base64_jwt(payload_fields)
    header_payload = (
        header_base64.decode("utf-8") + "." + payload_base64.decode("utf-8")
    )
    header_payload_base64 = str_to_b64(header_payload).encode("utf-8")

    signature_bytes: bytes = await wallet.sign_message(
        header_payload_base64, signing_key.verkey
    )
    signature_str = signature_bytes.decode("utf-8")
    header_payload_signature = header_payload + "." + signature_str
    return header_payload_signature