from ...config.injection_context import InjectionContext
from asynctest import TestCase as AsyncTestCase, mock as async_mock
from ...storage.basic import BasicStorage
from ...storage.base import BaseStorage

import hashlib
from marshmallow import fields
from unittest import mock, TestCase
import json

from ..thcf_model import *


class TestThcfCredentialRecord(AsyncTestCase):
    credential = {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://www.w3.org/2018/credentials/examples/v1",
        ],
        "id": "https://example.com/credentials/1872",
        "type": ["VerifiableCredential", "ConsentCredential"],
        "issuer": "https://example.edu/issuers/565049",
        "issuanceDate": "2010-01-01T19:23:24Z",
        "credentialSubject": {"value": "test"},
        "proof": {
            "jws": "anv/VWs3OnXUVvD88VLTCngf9wWT8ErIsXbB+JszOFUiqUaxapTPQ//br1qE6g/vUQWAWT7qH9oenTUQw5veCg"
        },
    }

    def assert_credential(self, credential):
        assert credential.context == self.credential["@context"]
        assert credential.id == self.credential["id"]
        assert credential.type == self.credential["type"]
        assert credential.issuer == self.credential["issuer"]
        assert credential.proof == self.credential["proof"]
        assert credential.credentialSubject == self.credential["credentialSubject"]

    async def testInit(self):
        context = InjectionContext()
        storage = BasicStorage()
        context.injector.bind_instance(BaseStorage, storage)

        record = THCFcreate_credential_from_dict(self.credential)
        self.assert_credential(record)
        record_id = await record.save(context)
        self.assert_credential(record)
