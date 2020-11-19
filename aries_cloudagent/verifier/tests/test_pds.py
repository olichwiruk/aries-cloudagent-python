import json
import pytest

from copy import deepcopy

from asynctest import TestCase as AsyncTestCase
from asynctest import mock as async_mock
from aries_cloudagent.wallet.basic import BasicWallet
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.wallet.base import BaseWallet
from ..pds import PDSVerifier
import collections

presentation_request = {
    "type": ["string"],
    "context": ["string"],
    "nonce": "6b1df3e3-55bc-4815-a4e3-848dd9414db6",
    "requested_attributes": {"test": {"restrictions": [{}]}},
}

presentation = {
    "context": ["string"],
    "id": "urn:uuid:cfd6e9f8-f22a-4643-acb7-59edb34e4157",
    "type": ["VerifiablePresentation", "string"],
    "verifiableCredential": [
        {
            "issuanceDate": "2020-11-18 11:28:38.240954Z",
            "type": ["VerifiableCredential", "string"],
            "proof": {
                "type": "Ed25519Signature2018",
                "created": "2020-11-18 11:28:38.259494Z",
                "proofPurpose": "assertionMethod",
                "verificationMethod": "3MTts9a3CqT9UYSzPJ9VcqWBDWTucW5GYZEENZAsNoY6",
                "jws": "e69ffac421099ee82cbfd8374a05beb031fc12aab99a0dedb54f2b2f9bf8b5dcecaa7c041041a169a37eb5fda25d7841dff7ca8b9aafaa6cce972e9d06b98307",
            },
            "issuer": "UFjZJF92Mp7BTyWiRiD2rP",
            "credentialSubject": {"test": "stuff", "id": "2EDzAU13hfgm57MHypVrHm"},
            "context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://www.schema.org",
            ],
        }
    ],
    "proof": {
        "type": "Ed25519Signature2018",
        "created": "2020-11-18 11:28:42.423088Z",
        "proofPurpose": "assertionMethod",
        "verificationMethod": "3QupoSDX3HBLdBYmHRJvcypGumoS4YqFG5N2dBPD6LSA",
        "jws": "bf5d055d15b94ee8da38b91d347036705b5178072cf1d0be3ddd0dd48d21585418b2b3a5e6a70caad967cebff071db98c15d9b1a88331065687b2e99d1f17a0e",
    },
}

presentation_string = '{"context": ["string"], "id": "urn:uuid:cfd6e9f8-f22a-4643-acb7-59edb34e4157", "type": ["VerifiablePresentation", "string"], "verifiableCredential": [{"issuanceDate": "2020-11-18 11:28:38.240954Z", "type": ["VerifiableCredential", "string"], "proof": {"type": "Ed25519Signature2018", "created": "2020-11-18 11:28:38.259494Z", "proofPurpose": "assertionMethod", "verificationMethod": "3MTts9a3CqT9UYSzPJ9VcqWBDWTucW5GYZEENZAsNoY6", "jws": "e69ffac421099ee82cbfd8374a05beb031fc12aab99a0dedb54f2b2f9bf8b5dcecaa7c041041a169a37eb5fda25d7841dff7ca8b9aafaa6cce972e9d06b98307"}, "issuer": "UFjZJF92Mp7BTyWiRiD2rP", "credentialSubject": {"test": "stuff", "id": "2EDzAU13hfgm57MHypVrHm"}, "context": ["https://www.w3.org/2018/credentials/v1", "https://www.schema.org"]}], "proof": {"type": "Ed25519Signature2018", "created": "2020-11-18 11:28:42.423088Z", "proofPurpose": "assertionMethod", "verificationMethod": "3QupoSDX3HBLdBYmHRJvcypGumoS4YqFG5N2dBPD6LSA", "jws": "bf5d055d15b94ee8da38b91d347036705b5178072cf1d0be3ddd0dd48d21585418b2b3a5e6a70caad967cebff071db98c15d9b1a88331065687b2e99d1f17a0e"}}'


class TestPDSVerifier(AsyncTestCase):
    def setUp(self):
        self.context: InjectionContext = InjectionContext()
        wallet = BasicWallet()
        self.verifier = PDSVerifier(wallet)
        # self.context.injector.bind_instance(BaseWallet, wallet)

    async def test_presentation_verification(self):
        pres = json.loads(
            presentation_string, object_pairs_hook=collections.OrderedDict
        )
        result = await self.verifier.verify_presentation(
            presentation_request, pres, {}, {}, {}, {}
        )
        assert result == True