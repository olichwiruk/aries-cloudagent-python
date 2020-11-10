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


class TestPDSHolder(AsyncTestCase):
    async def setUp(self):
        self.context: InjectionContext = InjectionContext()
        storage = BasicStorage()
        wallet = BasicWallet()
        issuer = PDSIssuer(wallet)
        self.credential = await create_test_credential(issuer)

        self.context.injector.bind_instance(BaseStorage, storage)
        self.context.injector.bind_instance(BaseWallet, wallet)
        self.holder = PDSHolder(self.context)

    async def test_create_presentation(self):
        request_presentation = {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://www.w3.org/2018/credentials/examples/v1",
            ],
            "id": "urn:uuid:3978344f-8596-4c3a-a978-8fcaba3903c5",
            "type": ["VerifiablePresentation", "CredentialManagerPresentation"],
            "verifiableCredential": [{}],
            "proof": [
                {
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
                    "verificationMethod": "6DpqHrFQtsAjxw73sjUVWgEYHX8tgWoSeAZm3tx9FULy",
                    "jws": "66ea5b361d4c479d06afd623e8d4a275cc501a3994400ecf41e8b347df19384e8acf8002684190aff7a289978dc26db7941819d0d99dad15ed3b22dbe7bd5f06",
                }
            ],
        }
        presentation = await self.holder.create_presentation(
            request_presentation, {}, {}, {}
        )
        assert 1 == presentation

    async def test_store_credential_retrieve_and_delete(self):
        cred_id = await self.holder.store_credential({}, self.credential, {})
        assert cred_id != None

        cred = await THCFCredential.retrieve_by_id(self.context, cred_id)
        cred_holder = await self.holder.get_credential(cred_id)
        assert cred.serialize(as_string=True) == cred_holder

        # check if dict fields are equal to record
        cred_serialized = cred.serialize()
        for key in self.credential:
            if key == "@context":
                assert self.credential[key] == cred_serialized["context"]
                continue
            assert self.credential[key] == cred_serialized[key]

        await self.holder.delete_credential(cred_id)
        with self.assertRaises(HolderError):
            cred = await self.holder.get_credential(cred_id)
