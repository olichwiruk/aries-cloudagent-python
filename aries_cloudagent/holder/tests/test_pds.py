import json

import pytest

from asynctest import TestCase as AsyncTestCase
from asynctest import mock as async_mock
from ..pds import *
from aries_cloudagent.storage.basic import BasicStorage
from ..models.credential import THCFCredential


credential_test_schema = {
    "@context": [
        "https://www.w3.org/2018/credentials/v1",
        "https://www.schema.org",
    ],
    "type": [
        "VerifiableCredential",
        "example",
    ],
    "issuer": "1234",
    "issuanceDate": "1234",
    "credentialSubject": {
        "id": "1234",
        "ocaSchema": {
            "dri": "1234",
            "dataDri": "1234",
        },
    },
    "proof": {
        "type": "Ed25519Signature2018",
        "created": "1234",
        "proofPurpose": "assertionMethod",
        "verificationMethod": "1234",
        "jws": "1234",
    },
}


class TestPDSIssuer(AsyncTestCase):
    async def setUp(self):
        self.context: InjectionContext = InjectionContext()
        storage = BasicStorage()
        self.context.injector.bind_instance(BaseStorage, storage)
        self.holder = PDSHolder(self.context)

    async def test_create_credential(self):
        cred_id = await self.holder.store_credential({}, credential_test_schema, {})
        assert cred_id != None

        cred = await THCFCredential.retrieve_by_id(self.context, cred_id)
        cred_holder = await self.holder.get_credential(cred_id)
        assert cred.serialize(as_string=True) == cred_holder

        # check if dict fields are equal to record
        cred_serialized = cred.serialize()
        for key in credential_test_schema:
            if key == "@context":
                assert credential_test_schema[key] == cred_serialized["context"]
                continue
            assert credential_test_schema[key] == cred_serialized[key]

        await self.holder.delete_credential(cred_id)
        with self.assertRaises(HolderError):
            cred = await self.holder.get_credential(cred_id)
