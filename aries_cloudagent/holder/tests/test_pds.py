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
