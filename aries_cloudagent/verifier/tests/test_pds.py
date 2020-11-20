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
from aries_cloudagent.storage.basic import BasicStorage
from aries_cloudagent.issuer.pds import PDSIssuer
from aries_cloudagent.holder.pds import PDSHolder
from aries_cloudagent.issuer.tests.test_pds import create_test_credential
from collections import OrderedDict

pres = OrderedDict(
    [
        ("context", ["string"]),
        ("id", "urn:uuid:e7cf488a-8c02-41e1-bee6-960195cec76d"),
        ("type", ["string", "VerifiablePresentation"]),
        (
            "verifiableCredential",
            [
                OrderedDict(
                    [
                        (
                            "context",
                            [
                                "https://www.w3.org/2018/credentials/v1",
                                "https://www.schema.org",
                            ],
                        ),
                        ("type", ["VerifiableCredential", "string"]),
                        ("issuer", "LW1dhhWfQnSAPGrQeFQJ19"),
                        ("issuanceDate", "2020-11-20 09:17:51.370730Z"),
                        (
                            "credentialSubject",
                            OrderedDict(
                                [("test", "stuff"), ("id", "B1cQNbS3Q3dYW3izkcuyHN")]
                            ),
                        ),
                        (
                            "proof",
                            OrderedDict(
                                [
                                    (
                                        "jws",
                                        "d5b5b8f7c58e38ca754a4faaed30887b4c6ec93b7d023094bb693ff7ace2ca5ff788b12451d88db4b8bc113119f7819f03a8f64c7b0bff676e9c0530458af20a",
                                    ),
                                    ("type", "Ed25519Signature2018"),
                                    ("created", "2020-11-20 09:17:51.391209Z"),
                                    ("proofPurpose", "assertionMethod"),
                                    (
                                        "verificationMethod",
                                        "3HZCVLBHJFcM1UmAtjkXzbsPiFV49GKHQa2oH5PdGHpG",
                                    ),
                                ]
                            ),
                        ),
                    ]
                )
            ],
        ),
        (
            "proof",
            OrderedDict(
                [
                    (
                        "jws",
                        "2943454495dd81679ea68f5c649151c056518e96ea510532d9318394124bd5f19e10d21e0e8a81e75467655a88268d153b9f8a7ebb82d6181cbc1727d29eb601",
                    ),
                    ("type", "Ed25519Signature2018"),
                    ("created", "2020-11-20 09:40:15.506419Z"),
                    ("proofPurpose", "assertionMethod"),
                    (
                        "verificationMethod",
                        "8fWWSVKWayfnH9XCEGrFkYnCozqyb6XtxPRvugZsY7AY",
                    ),
                ]
            ),
        ),
    ]
)

pres_request = {
    "type": ["string"],
    "context": ["string"],
    "nonce": "caf192b5-b7e1-4143-b1d9-a25acbe5d948",
    "requested_attributes": {"test": {"restrictions": [{}]}},
}


class TestPDSVerifier(AsyncTestCase):
    async def setUp(self):
        self.context: InjectionContext = InjectionContext()
        wallet = BasicWallet()
        storage = BasicStorage()
        issuer = PDSIssuer(wallet)
        holder = PDSHolder(wallet, storage)
        self.verifier = PDSVerifier(wallet)
        self.credential = await create_test_credential(issuer)
        self.cred_id = await holder.store_credential({}, self.credential, {})
        # self.requested_credentials = {
        #     "type": ["string"],
        #     "context": ["string"],
        #     "nonce": "caf192b5-b7e1-4143-b1d9-a25acbe5d948",
        #     "requested_attributes": {"test": {"restrictions": [{}]}},
        # }
        # self.presentation = await holder.create_presentation(
        #     presentation_request={
        #         "requested_attributes": {"test": {"restrictions": [{}]}}
        #     },
        #     requested_credentials=self.requested_credentials,
        #     schemas={},
        #     credential_definitions={},
        # )

        # self.context.injector.bind_instance(BaseWallet, wallet)

    async def test_presentation_verification(self):
        result = await self.verifier.verify_presentation(
            pres_request, pres, {}, {}, {}, {}
        )
        assert result == True