from .base import BasePersonalDataStorage
from .error import PDSNotFoundError
from .models.saved_personal_storage import SavedPersonalStorage
import hashlib
import multihash
import logging
import multibase
from aries_cloudagent.storage.error import StorageNotFoundError
from .models.table_that_matches_dris_with_pds import DriStorageMatchTable
from aries_cloudagent.aathcf.credentials import assert_type, assert_type_or
import json

LOGGER = logging.getLogger(__name__)


async def match_save_save_record_id(context, record_id, pds_name):
    match_table = DriStorageMatchTable(record_id, pds_name)
    record_id = await match_table.save(context)
    return record_id


async def match_table_query_id(context, id):
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
        raise PDSNotFoundError(err)

    return match


async def pds_get_active_name(context):
    try:
        active_pds = await SavedPersonalStorage.retrieve_active(context)
    except StorageNotFoundError as err:
        raise PDSNotFoundError(f"No active pds found {err.roll_up}")

    return active_pds.get_pds_name()


async def pds_get_by_name(context, name):
    pds: BasePersonalDataStorage = await context.inject(
        BasePersonalDataStorage, {"personal_storage_type": name}
    )

    return pds


async def pds_get_active(context):
    active_pds_name = await pds_get_active_name(context)
    pds = await pds_get_by_name(context, active_pds_name)
    return pds


async def pds_load(context, id: str) -> str:
    assert_type(id, str)

    # plugin = table_that_matches_plugins_with_ids.get(id, None)
    match = await match_table_query_id(context, id)
    pds = await pds_get_by_name(context, match.pds_type)
    result = await pds.load(id)

    return result


async def pds_save(context, payload, metadata: str = "{}") -> str:
    assert_type_or(payload, str, dict)
    assert_type(metadata, str)

    active_pds_name = await pds_get_active_name(context)
    pds = await pds_get_by_name(context, active_pds_name)
    payload_id = await pds.save(payload, json.loads(metadata))
    payload_id = await match_save_save_record_id(context, payload_id, active_pds_name)

    return payload_id


async def load_multiple(
    context, *, table: str = None, oca_schema_base_dri: str = None
) -> str:

    pds = await pds_get_active(context)
    result = await pds.load_multiple(
        table=table, oca_schema_base_dri=oca_schema_base_dri
    )
    assert_type(result, str)
    return result


async def delete_record(context, id: str) -> str:
    assert_type(id, str)

    match = await match_table_query_id(context, id)
    pds = await pds_get_by_name(context, match.pds_type)
    result = await pds.delete(id)

    return result


async def pds_get_usage_policy_if_active_pds_supports_it(context):
    active_pds_name = await pds_get_active_name(context)
    if active_pds_name[0] != "own_your_data":
        return None

    pds = await pds_get_by_name(context, active_pds_name)
    result = await pds.get_usage_policy()

    return result


def encode(data: str) -> str:
    hash_object = hashlib.sha256()
    hash_object.update(bytes(data, "utf-8"))
    multi = multihash.encode(hash_object.digest(), "sha2-256")
    result = multibase.encode("base58btc", multi)

    return result.decode("utf-8")
