import logging
import uuid
from marshmallow import Schema
from marshmallow.utils import INCLUDE
from typing import Tuple, Union
from ..core.error import BaseError
from .base import *
from .models.credential import *
from ..storage.base import BaseStorage, BaseStorageRecordSearch
from ..storage.error import StorageNotFoundError, StorageError
from ..config.injection_context import InjectionContext
from aries_cloudagent.wallet.base import BaseWallet
from ..messaging.valid import UUIDFour, IndyISO8601DateTime, JSONWebToken
from aries_cloudagent.aathcf.credentials import (
    CredentialSchema,
    PresentationSchema,
    PresentationRequestedAttributesSchema,
    PresentationRequestSchema,
    PresentationRequestedCredentialsSchema,
    PresentationSchema,
    verify_proof,
    create_proof,
)
import json
from collections import OrderedDict
from aries_cloudagent.storage.record import StorageRecord


def validate_schema(SchemaClass, schema: dict, exception=None):
    """
    Use Marshmallow Schema class to validate a schema in the form of dictionary
    and also handle fields like @context

    Returns errors if no exception passed
    or
    Throws passed in exception
    """
    test_schema = schema
    test_against = SchemaClass()
    # if isinstance(test_schema, OrderedDict):
    #     test_schema = dict(test_schema)
    if test_schema.get("@context") != None and test_schema.get("context") == None:
        test_schema = schema.copy()
        test_schema["context"] = test_schema.get("@context")
        test_schema.pop("@context", "skip errors")

    errors = test_against.validate(test_schema)
    if errors != {}:
        logging.getLogger(__name__).error(
            f"""Invalid Schema! errors: {errors} 
            schema: {test_schema}
            SchemaClass: {SchemaClass}"""
        )

        if exception != None:
            raise exception(f"""Invalid Schema! errors: {errors}""")
        else:
            return errors


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

        storage: BaseStorage = await self.context.inject(BaseStorage)
        try:
            record = await storage.get_record("THCFCredential", credential_id)
        except StorageError as err:
            raise HolderError(err.roll_up)

        return record.value

    async def delete_credential(self, credential_id: str):
        """
        Remove a credential stored in the wallet.

        Args:
            credential_id: Credential id to remove

        """
        storage: BaseStorage = await self.context.inject(BaseStorage)
        try:
            record = await storage.get_record("THCFCredential", credential_id)
            await storage.delete_record(record)
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

        validate_schema(PresentationRequestSchema, presentation_request, HolderError)
        validate_schema(
            PresentationRequestedCredentialsSchema, requested_credentials, HolderError
        )

        requested = presentation_request.get("requested_attributes")
        provided = requested_credentials.get("requested_attributes")

        # Check for missing fields
        # TODO: Should I be checking for missing fields?
        # maybe its fine to not provide all info
        # that probably should be handled in negotitation phase though?
        missing_fields = False
        for field in requested:
            provided_attribute = provided.get(field)
            if provided_attribute == None:
                missing_fields = True
                provided[field] = "Missing field"

        if missing_fields == True:
            raise HolderError("Some of the requested fields are missing!" + provided)

        # Retrieve specified credentials
        # TODO Add restrictions checking
        # TODO Change to credential_id
        credential_list = []
        for field in requested:
            provided_attribute = provided.get(field)
            cred_id = provided_attribute.get("cred_id")
            try:
                credential = await self.get_credential(cred_id)
            except HolderError as err:
                raise HolderError(
                    f"credential_id {cred_id} for field {field} is invalid"
                )
            credential = json.loads(credential, object_pairs_hook=OrderedDict)
            self.log("CREDENTIAL_LIST ITEM %s", credential)
            credential_list.append(credential)

        # Create type list
        request_type = ["VerifiablePresentation"]
        for i in presentation_request.get("type"):
            request_type.append(i)

        remove_duplicates = set(request_type)
        request_type = list(remove_duplicates)

        presentation = OrderedDict()
        presentation["context"] = presentation_request.get(
            "@context", presentation_request.get("context")
        )
        presentation["id"] = uuid.uuid4().urn
        presentation["type"] = request_type
        presentation["verifiableCredential"] = credential_list

        wallet = await self.context.inject(BaseWallet)
        proof = await create_proof(wallet, presentation, HolderError)
        presentation.update({"proof": proof})

        validate_schema(PresentationSchema, presentation, HolderError)

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
        self.log("store_credential invoked credential_data %s", credential_data)

        context = credential_data.get("@context")
        if context != None:
            credential_data["context"] = context
        errors = validate_schema(CredentialSchema, credential_data, HolderError)

        wallet = await self.context.inject(BaseWallet)
        if await verify_proof(wallet, credential_data) == False:
            raise HolderError("Proof is incorrect, could not verify")

        storage: BaseStorage = await self.context.inject(BaseStorage)
        try:
            record = StorageRecord("THCFCredential", json.dumps(credential_data))
            # TODO: TAGS?
            await storage.add_record(record)
        except StorageError as err:
            raise HolderError(err.roll_up)

        return record.id

    async def get_credentials(self) -> list:
        """
        Retrieve credential list based on a filter(TODO)

        """
        storage: BaseStorage = await self.context.inject(BaseStorage)
        try:
            search: BaseStorageRecordSearch = storage.search_records("THCFCredential")
            records = await search.fetch_all()
        except StorageError as err:
            raise HolderError(err.roll_up)

        credentials = []
        for i in records:
            cred = {"id": i.id, "credentials": i.value}
            credentials.append(cred)

        self.log("Credentials GET CREDENTIALS %s", credentials)

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
