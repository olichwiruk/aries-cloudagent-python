import logging

from ..config.base import BaseProvider, BaseInjector, BaseSettings
from ..utils.classloader import ClassLoader

LOGGER = logging.getLogger(__name__)


class PublicDataStorageProvider(BaseProvider):
    def __init__(self):
        self.cached_instances = {}

    STORAGE_TYPES = {
        "local": "aries_cloudagent.public_data_storage_thcf.local.LocalDataStorage",
        "data_vault": "aries_cloudagent.public_data_storage_thcf.data_vault.DataVault",
    }

    async def provide(self, settings: BaseSettings, injector: BaseInjector):
        # wallet_type = settings.get_value("wallet.type", default="basic").lower()
        # storage_default_type = "indy" if wallet_type == "indy" else "basic"
        # storage_type = settings.get_value(
        #     "storage_type", default=storage_default_type
        # ).lower()
        storage_type = settings.get("public_storage_type", "local")
        print("PublicDataStorage type", storage_type)

        if storage_type not in self.cached_instances:
            storage_class = self.STORAGE_TYPES.get(storage_type, storage_type)

            public_data_storage = ClassLoader.load_class(storage_class)
            self.cached_instances[storage_type] = public_data_storage()

            print("PublicDataStorage create", self.cached_instances)

        return self.cached_instances[storage_type]
