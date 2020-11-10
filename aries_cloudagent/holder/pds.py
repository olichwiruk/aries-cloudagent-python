import logging
from marshmallow import Schema
from marshmallow.utils import INCLUDE
from typing import Tuple, Union
from ..core.error import BaseError
from .base import *
from .models.credential import *
from ..storage.base import BaseStorage
from ..storage.error import StorageNotFoundError, StorageError
from ..config.injection_context import InjectionContext
from aries_cloudagent.wallet.base import BaseWallet
from ..messaging.valid import UUIDFour, IndyISO8601DateTime, JSONWebToken
from aries_cloudagent.aathcf.credentials import (
    CredentialSchema,
    PresentationSchema,
    verify_proof,
)


# TODO: Better error handling
class PDSHolder(BaseHolder):
    """It requires context with bound storage!
    # TODO: Maybe should consider manually packing
    records into storage so that only storage would be requiered?"""

    def __init__(self, context):
        self.log = logging.getLogger(__name__).info
        self.context: InjectionContext = context

    async def get_credential(self, credential_id: str) -> str:
        """
        Get a stored credential.

        Args:
            credential_id: Credential id to retrieve

        """
        self.log("get_credential invoked")

        try:
            credential: THCFCredential = await THCFCredential.retrieve_by_id(
                self.context, credential_id
            )
        except StorageError as err:
            raise HolderError(err.roll_up)

        return credential.serialize(as_string=True)

    async def delete_credential(self, credential_id: str):
        """
        Remove a credential stored in the wallet.

        Args:
            credential_id: Credential id to remove

        """
        self.log("delete_credential invoked")

        try:
            credential: THCFCredential = await THCFCredential.retrieve_by_id(
                self.context, credential_id
            )
            await credential.delete_record(self.context)
        except StorageError as err:
            raise HolderError(err.roll_up)

    async def get_mime_type(
        self, credential_id: str, attr: str = None
    ) -> Union[dict, str]:
        """
        Get MIME type per attribute (or for all attributes).

        Args:
            credential_id: credential id
            attr: attribute of interest or omit for all

        Returns: Attribute MIME type or dict mapping attribute names to MIME types
            attr_meta_json = all_meta.tags.get(attr)

        """
        pass

    async def create_presentation(
        self,
        presentation_request: dict,
        requested_credentials: dict,
        schemas: dict,
        credential_definitions: dict,
        rev_states: dict = None,
    ) -> str:
        """
        Get credentials stored in the wallet.

        Args:
            presentation_request: Valid indy format presentation request
            requested_credentials: Indy format requested credentials
            schemas: Indy formatted schemas JSON
            credential_definitions: Indy formatted credential definitions JSON
            rev_states: Indy format revocation states JSON
        """
        if presentation_request.get("@context") != None:
            presentation_request["context"] = presentation_request.get("@context")
            presentation_request.pop("@context", "skip error")

        self.log(
            "Validation: ",
        )
        pres = PresentationSchema()
        pres = pres.validate(presentation_request)
        return pres

    #     {
    #         "name": string,
    #         "version": string,
    #         "nonce": string, - a big number represented as a string (use `generate_nonce` function to generate 80-bit number)
    #         "requested_attributes": { // set of requested attributes
    #              "<attr_referent>": <attr_info>, // see below
    #              ...,
    #         },
    #         "requested_predicates": { // set of requested predicates
    #              "<predicate_referent>": <predicate_info>, // see below
    #              ...,
    #          },
    #         "non_revoked": Optional<<non_revoc_interval>>, // see below,
    #                        // If specified prover must proof non-revocation
    #                        // for date in this interval for each attribute
    #                        // (applies to every attribute and predicate but can be overridden on attribute level)
    #                        // (can be overridden on attribute level)
    #     }
    # :param requested_credentials_json: either a credential or self-attested attribute for each requested attribute
    #     {
    #         "self_attested_attributes": {
    #             "self_attested_attribute_referent": string
    #         },
    #         "requested_attributes": {
    #             "requested_attribute_referent_1": {"cred_id": string, "timestamp": Optional<number>, revealed: <bool> }},
    #             "requested_attribute_referent_2": {"cred_id": string, "timestamp": Optional<number>, revealed: <bool> }}
    #         },
    #         "requested_predicates": {
    #             "requested_predicates_referent_1": {"cred_id": string, "timestamp": Optional<number> }},
    #         }
    #     }

    async def create_credential_request(
        self, credential_offer: dict, credential_definition: dict, holder_did: str
    ) -> Tuple[str, str]:
        """
        Create a credential request for the given credential offer.

        Args:
            credential_offer: The credential offer to create request for
            credential_definition: The credential definition to create an offer for
            holder_did: the DID of the agent making the request

        Returns:
            A tuple of the credential request and credential request metadata

        """
        pass

    async def store_credential(
        self,
        credential_definition: dict,
        credential_data: dict,
        credential_request_metadata: dict,
        credential_attr_mime_types=None,
        credential_id: str = None,
        rev_reg_def: dict = None,
    ):
        """
        Store a credential in the wallet.

        Args:
            credential_definition: Credential definition for this credential
            credential_data: Credential data generated by the issuer
            credential_request_metadata: credential request metadata generated
                by the issuer
            credential_attr_mime_types: dict mapping attribute names to (optional)
                MIME types to store as non-secret record, if specified
            credential_id: optionally override the stored credential id
            rev_reg_def: revocation registry definition in json

        Returns:
            the ID of the stored credential

        """
        self.log("store_credential invoked credential_data %s", credential_data)

        credential_copy = credential_data.copy()

        if (
            credential_copy.get("@context") != None
            and credential_copy.get("context") == None
        ):
            credential_copy["context"] = credential_copy.get("@context")
            credential_copy.pop("@context", "skip errors")

        credential_schema = CredentialSchema()
        errors = credential_schema.validate(credential_copy)
        if errors != {}:
            raise HolderError(errors)

        wallet = await self.context.inject(BaseWallet)
        isVerified = await verify_proof(wallet, credential_data)
        if isVerified == False:
            raise HolderError("Proof is incorrect, could not verify")

        credential = THCFCredential(
            issuanceDate=credential_data.get("issuanceDate"),
            credentialSubject=credential_data.get("credentialSubject"),
            context=credential_data.get("@context"),
            issuer=credential_data.get("issuer"),
            proof=credential_data.get("proof"),
            type=credential_data.get("type"),
            id=credential_data.get("id"),
        )

        id = await credential.save(self.context, reason="Credential saved to storage")
        self.log("Saved Credential id: %s serialized %s", id, credential.serialize())

        return id

    async def get_credentials(self) -> list:
        """
        Retrieve credential list based on a filter(TODO)

        """
        self.log("get_credential invoked")

        try:
            credentials: THCFCredential = await THCFCredential.query(self.context)
        except StorageError as err:
            raise HolderError(err.roll_up)

        result = []
        for cred in credentials:
            result.append(cred.serialize())

        return result

    async def create_revocation_state(
        self,
        cred_rev_id: str,
        rev_reg_def: dict,
        rev_reg_delta: dict,
        timestamp: int,
        tails_file_path: str,
    ) -> str:
        """
        Create current revocation state for a received credential.

        Args:
            cred_rev_id: credential revocation id in revocation registry
            rev_reg_def: revocation registry definition
            rev_reg_delta: revocation delta
            timestamp: delta timestamp

        Returns:
            the revocation state

        """
        pass
