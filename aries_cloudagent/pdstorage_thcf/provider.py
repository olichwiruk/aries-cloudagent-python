import logging

from ..config.base import BaseProvider, BaseInjector, BaseSettings
from ..utils.classloader import ClassLoader

LOGGER = logging.getLogger(__name__)


class PersonalDataStorageProvider(BaseProvider):
    def __init__(self):
        self.cached_instances = {}

    async def provide(self, settings: BaseSettings, injector: BaseInjector):
        storage_type = settings.get("personal_storage_type")
        registered_types = settings.get("personal_storage_registered_types")

        print("PersonalDataStorage type", storage_type)
        assert storage_type != None, "Bug in active personal_storage_type, it's None"

        if storage_type not in self.cached_instances:
            storage_class = registered_types.get(storage_type)
            assert storage_class != None, "Storage type / class is not registered"

            public_data_storage = ClassLoader.load_class(storage_class)
            self.cached_instances[storage_type] = public_data_storage()

            print("PersonalDataStorage create", self.cached_instances)

        return self.cached_instances[storage_type]
