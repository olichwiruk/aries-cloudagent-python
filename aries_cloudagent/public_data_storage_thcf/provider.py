import logging

from ..config.base import BaseProvider, BaseInjector, BaseSettings
from ..utils.classloader import ClassLoader

LOGGER = logging.getLogger(__name__)


class PublicDataStorageProvider(BaseProvider):
    def __init__(self):
        self.cached_instances = {}

    async def provide(self, settings: BaseSettings, injector: BaseInjector):
        storage_type = settings.get("public_storage_type", "local")
        registered_types = settings.get("public_storage_registered_types")
        print("PublicDataStorage type", storage_type)

        if storage_type not in self.cached_instances:
            storage_class = registered_types.get(storage_type)

            public_data_storage = ClassLoader.load_class(storage_class)
            self.cached_instances[storage_type] = public_data_storage()

            print("PublicDataStorage create", self.cached_instances)

        return self.cached_instances[storage_type]
