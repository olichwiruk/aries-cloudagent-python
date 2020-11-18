import json
import logging
import nacl
from typing import Sequence, Tuple

from ..wallet.crypto import sign_message, verify_signed_message
from ..wallet.base import BaseWallet, KeyInfo
from ..connections.models.connection_record import ConnectionRecord

from .base import (
    BaseIssuer,
    IssuerError,
    IssuerRevocationRegistryFullError,
    DEFAULT_CRED_DEF_TAG,
    DEFAULT_SIGNATURE_TYPE,
)
from aries_cloudagent.wallet.util import bytes_to_b64
from ..messaging.util import time_now
from aries_cloudagent.wallet.error import WalletError
from ..aathcf.credentials import create_proof
from aries_cloudagent.holder.pds import validate_schema
from aries_cloudagent.aathcf.credentials import CredentialSchema
from collections import OrderedDict


class PDSIssuer(BaseIssuer):
    def __init__(self, wallet: BaseWallet):
        """
        Initialize an PDSIssuer instance.

        Args:


        """
        self.wallet: BaseWallet = wallet
        self.log = logging.getLogger(__name__).info

    def make_schema_id(
        self, origin_did: str, schema_name: str, schema_version: str
    ) -> str:
        """Derive the ID for a schema."""
        return f"{origin_did}:2:{schema_name}:{schema_version}"

    async def create_and_store_schema(
        self,
        origin_did: str,
        schema_name: str,
        schema_version: str,
        attribute_names: Sequence[str],
    ) -> Tuple[str, str]:
        """
        Create a new credential schema and store it in the wallet.

        Args:
            origin_did: the DID issuing the credential definition
            schema_name: the schema name
            schema_version: the schema version
            attribute_names: a sequence of schema attribute names

        Returns:
            A tuple of the schema ID and JSON

        """

        pass
        return (schema_id, schema_json)

    def make_credential_definition_id(
        self, origin_did: str, schema: dict, signature_type: str = None, tag: str = None
    ) -> str:
        """Derive the ID for a credential definition."""
        signature_type = signature_type or DEFAULT_SIGNATURE_TYPE
        tag = tag or DEFAULT_CRED_DEF_TAG
        return f"{origin_did}:3:{signature_type}:{str(schema['seqNo'])}:{tag}"

    async def credential_definition_in_wallet(
        self, credential_definition_id: str
    ) -> bool:
        """
        Check whether a given credential definition ID is present in the wallet.

        Args:
            credential_definition_id: The credential definition ID to check
        """
        pass
        return False

    async def create_and_store_credential_definition(
        self,
        origin_did: str,
        schema: dict,
        signature_type: str = None,
        tag: str = None,
        support_revocation: bool = False,
    ) -> Tuple[str, str]:
        """
        Create a new credential definition and store it in the wallet.

        Args:
            origin_did: the DID issuing the credential definition
            schema: the schema used as a basis
            signature_type: the credential definition signature type (default 'CL')
            tag: the credential definition tag
            support_revocation: whether to enable revocation for this credential def

        Returns:
            A tuple of the credential definition ID and JSON

        """

        pass
        return (credential_definition_id, credential_definition_json)

    async def create_credential_offer(self, credential_definition_id: str) -> str:
        """
        Create a credential offer for the given credential definition id.

        Args:
            credential_definition_id: The credential definition to create an offer for

        Returns:
            The created credential offer

        """
        pass

        return credential_offer_json

    async def create_credential(
        self,
        schema: dict,
        credential_offer: dict,
        credential_request: dict,
        credential_values: dict,
        revoc_reg_id: str = None,
        tails_file_path: str = None,
    ) -> Tuple[str, str]:
        """
        Create a credential.

        Args
            schema: Schema to create credential for
            credential_offer: Credential Offer to create credential for
            credential_request: Credential request to create credential for
            credential_values: Values to go in credential
            revoc_reg_id: ID of the revocation registry
            tails_file_path: Path to the local tails file

        Returns:
            A tuple of created credential and revocation id

        """
        self.log("create_credential invoked")

        credential_type = schema.get("credential_type")
        connection_record: ConnectionRecord = credential_request.get(
            "connection_record"
        )

        my_did = connection_record.my_did
        their_did = connection_record.their_did
        if None in [my_did, their_did]:
            raise IssuerError(
                f"""You don't have a established did with this connection
                or they don't have a did, your_did {my_did}, their_did {their_did}"""
            )
        if None or {} in [schema, credential_values, connection_record]:
            raise IssuerError(
                f"""[schema, credential_values, connection_record] {[schema, credential_values, connection_record]} some of these need to be filled in """
            )

        credential_values.update({"id": their_did})
        credential_dict = OrderedDict()
        # TODO: Point to some OCA Credential schema

        # This documents should exist, those should be cached
        # it seems to be establishing a semantic context, meaning
        # that it contains explanations of what credential fields mean
        # and what credential fields and types are possible
        # We should create it and it should be unchanging so that you can
        # cache it
        # if words in context overlapp, we should read the contexts from
        # top to bottom, so that later contexts overwrite earlier contexts
        credential_dict["context"] = [
            "https://www.w3.org/2018/credentials/v1",
            "https://www.schema.org",
        ]

        # This partly seems to be an extension of context
        # for example URI = https://www.schema.org has a json
        # and that json has VerifiableCredential with all possible fields
        # which we can reach through https://www.schema.org/VerifiableCredential
        credential_dict["type"] = ["VerifiableCredential", credential_type]
        credential_dict["issuer"] = my_did
        credential_dict["issuanceDate"] = time_now()
        credential_dict["credentialSubject"] = credential_values
        # "credentialSubject": {
        #     # This should point to some info about the subject of credenial?
        #     # machine readable document, about the subjecty
        #     "id": "Did of subject",
        #     "ocaSchema": {
        #         "dri": "1234",
        #         "dataDri": "1234",
        #     },
        credential_dict["proof"] = await create_proof(
            self.wallet, credential_dict, IssuerError
        )
        self.log("Proof dictionary: %s", credential_dict)

        validate_schema(CredentialSchema, credential_dict, IssuerError)

        return json.dumps(credential_dict), None

    async def revoke_credentials(
        self, revoc_reg_id: str, tails_file_path: str, cred_revoc_ids: Sequence[str]
    ) -> (str, Sequence[str]):
        """
        Revoke a set of credentials in a revocation registry.

        Args:
            revoc_reg_id: ID of the revocation registry
            tails_file_path: path to the local tails file
            cred_revoc_ids: sequences of credential indexes in the revocation registry

        Returns:
            Tuple with the combined revocation delta, list of cred rev ids not revoked

        """
        pass

    async def merge_revocation_registry_deltas(
        self, fro_delta: str, to_delta: str
    ) -> str:
        """
        Merge revocation registry deltas.

        Args:
            fro_delta: original delta in JSON format
            to_delta: incoming delta in JSON format

        Returns:
            Merged delta in JSON format

        """

        pass

    async def create_and_store_revocation_registry(
        self,
        origin_did: str,
        cred_def_id: str,
        revoc_def_type: str,
        tag: str,
        max_cred_num: int,
        tails_base_path: str,
    ) -> Tuple[str, str, str]:
        """
        Create a new revocation registry and store it in the wallet.

        Args:
            origin_did: the DID issuing the revocation registry
            cred_def_id: the identifier of the related credential definition
            revoc_def_type: the revocation registry type (default CL_ACCUM)
            tag: the unique revocation registry tag
            max_cred_num: the number of credentials supported in the registry
            tails_base_path: where to store the tails file

        Returns:
            A tuple of the revocation registry ID, JSON, and entry JSON

        """

        pass
