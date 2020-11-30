import json
import logging
import uuid
from collections import OrderedDict
from typing import Tuple, Union

from aries_cloudagent.aathcf.credentials import (
    CredentialSchema,
    PresentationRequestSchema,
    PresentationSchema,
    create_proof,
    validate_schema,
    verify_proof,
)
from aries_cloudagent.storage.record import StorageRecord

from ..storage.base import BaseStorageRecordSearch
from ..storage.error import StorageError
from .base import BaseHolder, HolderError


# TODO: Better error handling
class PDSHolder(BaseHolder):
    def __init__(self, wallet, storage):
        self.logger = logging.getLogger(__name__)
        self.wallet = wallet
        self.storage = storage

    async def get_credential(self, credential_id: str) -> str:
        """
        Get a stored credential.

        Args:
            credential_id: Credential id to retrieve

        """

        try:
            record = await self.storage.get_record("THCFCredential", credential_id)
        except StorageError as err:
            raise HolderError(err.roll_up)

        return record.value

    async def delete_credential(self, credential_id: str):
        """
        Remove a credential stored in the wallet.

        Args:
            credential_id: Credential id to remove

        """
        try:
            record = await self.storage.get_record("THCFCredential", credential_id)
            await self.storage.delete_record(record)
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

        validate_schema(
            PresentationRequestSchema,
            presentation_request,
            HolderError,
            self.logger.error,
        )

        requested = presentation_request.get("requested_attributes")
        credential_id = requested_credentials.get("credential_id")

        if credential_id is None:
            raise HolderError("Provided credentials are empty " + requested_credentials)

        """

        Retrieve credentials which were provided by the user

        """

        try:
            credential = await self.get_credential(credential_id)
        except HolderError as err:
            raise HolderError(f"credential_id {credential_id} is invalid {err.roll_up}")
        credential = json.loads(credential, object_pairs_hook=OrderedDict)

        """

        Check if credential has what it needs to have

        TODO: caching credentials of same credential_id so there wont be duplicates
        or maybe set will do

        TODO: this checking is very shallow, we need something robust

        """
        for field in requested:
            if field not in credential["credentialSubject"]:
                raise HolderError(
                    f"Specified credential doesn't have the requested attribute\n"
                    f"Credential === {credential}\n"
                    f"requested attributes === {requested}\n"
                    f"Requested_field === {field}\n"
                )

        """

        Process Context and type so that they are non repeating and
        requested context, type are more important / have higher indexes

        """

        # TYPE
        request_type = presentation_request.get("type")
        processed_type = ["VerifiablePresentation"]
        if isinstance(request_type, list) and request_type != []:
            processed_type.extend(request_type)
            remove_duplicates = set(processed_type)
            processed_type = list(remove_duplicates)

        # CONTEXT
        request_context = presentation_request.get(
            "@context", presentation_request.get("context")
        )
        processed_context = [
            "https://www.w3.org/2018/credentials/v1",
            "https://www.w3.org/2018/credentials/examples/v1",
        ]
        if isinstance(request_context, list) and request_context != []:
            processed_context.extend(request_context)
            remove_duplicates = set(processed_context)
            processed_context = list(remove_duplicates)

        """

        Create the presentation

        """

        presentation = OrderedDict()
        presentation["context"] = processed_context
        presentation["id"] = uuid.uuid4().urn
        presentation["type"] = processed_type
        presentation["verifiableCredential"] = {credential_id: credential}

        proof = await create_proof(self.wallet, presentation, HolderError)
        presentation.update({"proof": proof})

        validate_schema(
            PresentationSchema, presentation, HolderError, self.logger.error
        )

        return json.dumps(presentation)

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
        self.logger.debug(
            "store_credential invoked credential_data %s", credential_data
        )

        context = credential_data.get("@context")
        if context is not None:
            credential_data["context"] = context
        validate_schema(
            CredentialSchema, credential_data, HolderError, self.logger.error
        )

        if await verify_proof(self.wallet, credential_data) is False:
            raise HolderError("Proof is incorrect, could not verify")

        try:
            record = StorageRecord("THCFCredential", json.dumps(credential_data))
            # TODO: TAGS?
            await self.storage.add_record(record)
        except StorageError as err:
            raise HolderError(err.roll_up)

        return record.id

    async def get_credentials(self) -> list:
        """
        Retrieve credential list based on a filter(TODO)

        FIXME This is ideally only for debug? so maybe pages are not
        needed

        """
        try:
            search: BaseStorageRecordSearch = self.storage.search_records(
                "THCFCredential"
            )
            records = await search.fetch_all()
        except StorageError as err:
            raise HolderError(err.roll_up)

        credentials = []
        for i in records:
            cred = {"id": i.id, "credential": i.value}
            credentials.append(cred)

        self.logger.debug("Credentials GET CREDENTIALS %s", credentials)

        return credentials

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
