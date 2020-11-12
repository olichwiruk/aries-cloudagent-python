from ..credentials import create_proof_jwt
from aries_cloudagent.wallet.basic import BasicWallet
from asynctest import TestCase as AsyncTestCase


class TestJWT(AsyncTestCase):
    async def setUp(self):
        self.wallet = BasicWallet()
        self.example_schema = {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://www.w3.org/2018/credentials/examples/v1",
            ],
            "type": ["VerifiablePresentation"],
            "verifiableCredential": [{}],
            "proof": {},
        }

    async def test_create_proof_jwt(self):
        abc = await create_proof_jwt(self.wallet, self.example_schema)
        assert (
            abc
            == "eyJpc3MiOiJqb2UiLA0KICJleHAiOjEzMDA4MTkzODAsDQogImh0dHA6Ly9leGFtcGxlLmNvbS9pc19yb290Ijp0cnVlfQ"
        )
        assert abc == "eyJ0eXAiOiJKV1QiLA0KICJhbGciOiJIUzI1NiJ9"