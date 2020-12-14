from .base import BasePersonalDataStorage
from .error import PersonalDataStorageNotFoundError
from .models.saved_personal_storage import SavedPersonalStorage
import hashlib
import multihash
import logging
import multibase
from aries_cloudagent.storage.error import StorageNotFoundError
from .models.table_that_matches_dris_with_pds import DriStorageMatchTable
from aries_cloudagent.aathcf.credentials import assert_type

LOGGER = logging.getLogger(__name__)


async def pds_get_active_pds_name(context):
    try:
        active_pds = await SavedPersonalStorage.retrieve_active(context)
    except StorageNotFoundError as err:
        raise PersonalDataStorageNotFoundError(f"No active pds found {err.roll_up}")

    return active_pds.get_pds_name


async def load_string(context, id: str) -> str:
    assert_type(id, str)

    # plugin = table_that_matches_plugins_with_ids.get(id, None)
    try:
        match = await DriStorageMatchTable.retrieve_by_id(context, id)
    except StorageNotFoundError as err:
        LOGGER.error(
            f"table_that_matches_plugins_with_ids id that matches with None value\n",
            f"input id: {id}\n",
            f"ERROR: {err.roll_up}",
        )
        debug_all_records = await DriStorageMatchTable.query(context)
        LOGGER.error("All records in table: ", debug_all_records)
        raise PersonalDataStorageNotFoundError(err)

    pds: BasePersonalDataStorage = await context.inject(
        BasePersonalDataStorage, {"personal_storage_type": match.pds_type}
    )
    result = await pds.load(id)

    return result


async def save_string(context, payload: str, metadata="{}") -> str:
    assert_type(payload, str)
    assert_type(metadata, str)

    active_pds_name = await pds_get_active_pds_name()

    pds: BasePersonalDataStorage = await context.inject(
        BasePersonalDataStorage, {"personal_storage_type": active_pds_name}
    )
    payload_id = await pds.save(payload, metadata)

    match_table = DriStorageMatchTable(payload_id, active_pds_name)
    payload_id = await match_table.save(context)

    return payload_id


async def load_table(context, table: str) -> str:
    assert_type(table, str)

    active_pds_name = await pds_get_active_pds_name()

    pds: BasePersonalDataStorage = await context.inject(
        BasePersonalDataStorage, {"personal_storage_type": active_pds_name}
    )

    result = await pds.load_table(table)

    assert_type(result, str)
    return result


async def delete_record(context, id: str) -> str:
    assert_type(id, str)

    try:
        match = await DriStorageMatchTable.retrieve_by_id(context, id)
    except StorageNotFoundError as err:
        LOGGER.error(
            f"table_that_matches_plugins_with_ids id that matches with None value\n",
            f"input id: {id}\n",
            f"plugin: {match}",
            f"ERROR: {err.roll_up}",
        )
        raise PersonalDataStorageNotFoundError(err)

    pds: BasePersonalDataStorage = await context.inject(
        BasePersonalDataStorage, {"personal_storage_type": match.pds_type}
    )
    result = await pds.delete(id)

    return result


async def pds_get_usage_policy_if_active_pds_supports_it(context):
    active_pds_name = await pds_get_active_pds_name(context)
    if active_pds_name[0] != "own_your_data":
        return None

    pds: BasePersonalDataStorage = await context.inject(
        BasePersonalDataStorage, {"personal_storage_type": active_pds_name}
    )

    result = await pds.get_usage_policy()

    return result


def encode(data: str) -> str:
    hash_object = hashlib.sha256()
    hash_object.update(bytes(data, "utf-8"))
    multi = multihash.encode(hash_object.digest(), "sha2-256")
    result = multibase.encode("base58btc", multi)

    return result.decode("utf-8")
