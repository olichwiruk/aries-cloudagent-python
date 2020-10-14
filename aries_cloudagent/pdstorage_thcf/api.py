from .base import BasePersonalDataStorage
from .error import *
from ..messaging.request_context import RequestContext
import hashlib
import multihash
import multibase

table_that_matches_plugins_with_ids = {}


async def load_string(context: RequestContext, id: str, pds_type: str = None):
    if id == None:
        return None
    id = str(id)

    if pds_type != None:
        plugin = pds_type

    else:
        plugin = table_that_matches_plugins_with_ids.get(id)
        if plugin == None:
            return None

    pds: BasePersonalDataStorage = await context.inject(
        BasePersonalDataStorage, {"personal_storage_type": plugin}
    )
    result = await pds.load(id)

    return result


async def save_string(context: RequestContext, payload: str):
    if payload == None:
        return None

    pds: BasePersonalDataStorage = await context.inject(BasePersonalDataStorage)
    active_plugin = context.settings.get("personal_storage_type")

    print("Payload: ", payload)
    payload_id = await pds.save(payload)
    payload_id = str(payload_id)

    table_that_matches_plugins_with_ids[payload_id] = active_plugin

    return payload_id


def encode(data: str) -> str:
    hash_object = hashlib.sha256()
    hash_object.update(bytes(data, "utf-8"))
    multi = multihash.encode(hash_object.digest(), "sha2-256")
    result = multibase.encode("base58btc", multi)

    return result.decode("utf-8")


# def get_hash_info(data: bytes) -> tuple:
#     data = multibase.decode(data)
#     data = multihash.decode(data)
#     return data

