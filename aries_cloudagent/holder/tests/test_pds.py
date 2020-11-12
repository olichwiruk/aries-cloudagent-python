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


class TestPDSHolder(AsyncTestCase):
    async def setUp(self):
        self.context: InjectionContext = InjectionContext()
        storage = BasicStorage()
        self.wallet = BasicWallet()
        issuer = PDSIssuer(self.wallet)
        self.credential = await create_test_credential(issuer)

        self.context.injector.bind_instance(BaseStorage, storage)
        self.context.injector.bind_instance(BaseWallet, self.wallet)
        self.holder = PDSHolder(self.context)

    async def test_create_presentation(self):
        cred_id = await self.holder.store_credential({}, self.credential, {})
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
                "first_name": {"cred_id": cred_id, "revealed": True},
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

        presentation = await self.holder.create_presentation(
            presentation_request, requested_credentials, {}, {}
        )
        assert await verify_proof(self.wallet, presentation) == True
        assert isinstance(presentation["id"], str)
        assert presentation["id"].startswith("urn:uuid:")
        assert presentation["@context"] == presentation_example["@context"]
        assert "VerifiablePresentation" in presentation["type"]

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
