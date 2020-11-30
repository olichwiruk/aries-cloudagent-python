import json

import pytest

from asynctest import TestCase as AsyncTestCase
from asynctest import mock as async_mock
from ..pds import *
from aries_cloudagent.storage.basic import BasicStorage
from ..models.credential import THCFCredential
from aries_cloudagent.wallet.basic import BasicWallet
from aries_cloudagent.issuer.pds import PDSIssuer
from aries_cloudagent.connections.models.connection_record import ConnectionRecord
from ...issuer.tests.test_pds import create_test_credential
from aries_cloudagent.messaging.util import time_now

presentation_request = {
    "@context": [
        "https://www.w3.org/2018/credentials/v1",
        "https://www.w3.org/2018/credentials/examples/v1",
    ],
    "type": ["VerifiablePresentation", "CredentialManagerPresentation"],
    "nonce": "1234678",
    "requested_attributes": {
        "first_name": {"restrictions": [{"issuer_did": "1234"}]},
    },
}

requested_credentials = {
    "requested_attributes": {
        "first_name": {"cred_id": "1234", "revealed": True},
    },
    # "requested_predicates": {}, TODO
    # "self_attested_attributes": {}, TODO
}

presentation_example = {
    "@context": [
        "https://www.w3.org/2018/credentials/v1",
        "https://www.w3.org/2018/credentials/examples/v1",
    ],
    "type": ["VerifiablePresentation"],
    "verifiableCredential": [{}],
    "proof": {},
}


class TestPDSHolder(AsyncTestCase):
    async def setUp(self):
        self.context: InjectionContext = InjectionContext()
        storage = BasicStorage()
        self.wallet = BasicWallet()
        self.holder = PDSHolder(self.wallet, storage)
        issuer = PDSIssuer(self.wallet)

        self.context.injector.bind_instance(BaseWallet, self.wallet)

        self.credential = await create_test_credential(issuer)
        self.cred_id = await self.holder.store_credential({}, self.credential, {})

    async def test_retrieve_records_are_the_same(self):
        cred_holder = await self.holder.get_credential(self.cred_id)
        assert isinstance(cred_holder, str)
        cred_holder_json = json.loads(cred_holder)
        assert cred_holder_json == self.credential

    async def test_store_credential_retrieve_and_delete(self):
        cred = await self.holder.get_credential(self.cred_id)
        cred_serialized = json.loads(cred)
        assert cred_serialized == self.credential

        await self.holder.delete_credential(self.cred_id)
        with self.assertRaises(HolderError):
            cred = await self.holder.get_credential(self.cred_id)
        with self.assertRaises(HolderError):
            cred = await self.holder.delete_credential(self.cred_id)

    async def test_invalid_parameters_getters(self):
        with self.assertRaises(HolderError):
            cred = await self.holder.get_credential("12")

        with self.assertRaises(HolderError):
            await self.holder.delete_credential("34")

    async def test_invalid_parameters_create_pres(self):
        schema_with_credential_ids = requested_credentials.copy()
        schema_with_credential_ids["requested_attributes"]["first_name"][
            "cred_id"
        ] = self.cred_id

        with self.assertRaises(HolderError):
            await self.holder.create_presentation(
                {}, schema_with_credential_ids, {}, {}
            )
        with self.assertRaises(HolderError):
            await self.holder.create_presentation(presentation_request, {}, {}, {})

    async def test_create_presentation(self):
        cred = requested_credentials.copy()
        cred["requested_attributes"]["first_name"]["cred_id"] = self.cred_id
        presentation = await self.holder.create_presentation(
            presentation_request, cred, {}, {}
        )
        presentation = json.loads(presentation)
        assert await verify_proof(self.wallet, presentation) == True
        assert isinstance(presentation["id"], str)
        assert presentation["id"].startswith("urn:uuid:")
        assert presentation["context"] == presentation_example["@context"]
        assert len(presentation["type"]) == 2
        assert len(presentation["context"]) == 2

    async def test_create_presentation_invalid_parameters_passed(self):
        with self.assertRaises(HolderError):
            await self.holder.create_presentation(
                presentation_request, requested_credentials, {}, {}
            )

        with self.assertRaises(HolderError):
            request = presentation_request.copy()
            request.pop("@context")
            await self.holder.create_presentation(
                request, requested_credentials, {}, {}
            )

        with self.assertRaises(HolderError):
            request = presentation_request.copy()
            request.pop("requested_attributes")
            await self.holder.create_presentation(
                request, requested_credentials, {}, {}
            )
