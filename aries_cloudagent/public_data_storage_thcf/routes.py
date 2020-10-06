import logging
import json

from aiohttp import web
from aiohttp_apispec import (
    docs,
    match_info_schema,
    querystring_schema,
    request_schema,
    response_schema,
)

from marshmallow import fields, validate, Schema
from .base import PublicDataStorage
from .error import *


class SaveRecordSchema(Schema):
    payload = fields.Str(required=False)


class SetActiveStorageTypeSchema(Schema):
    type = fields.Str(required=True)


@docs(tags=["Public Data Storage"], summary="Save data in a public data storage")
@request_schema(SaveRecordSchema())
async def save_record(request: web.BaseRequest):
    context = request.app["request_context"]
    body = await request.json()

    payload = body.get("payload", None)
    assert payload != None
    print("payload: ", payload)

    public_storage: PublicDataStorage = await context.inject(PublicDataStorage)

    try:
        payload_id = await public_storage.save(payload)
    except PublicDataStorageError as err:
        raise web.HTTPError(reason=err.roll_up)

    return web.json_response({"payload_id": payload_id})


@docs(
    tags=["Public Data Storage"],
    summary="Retrieve data from a public data storage using data id",
)
async def get_record(request: web.BaseRequest):
    context = request.app["request_context"]
    payload_id = request.match_info["payload_id"]

    assert payload_id != None

    public_storage: PublicDataStorage = await context.inject(PublicDataStorage)

    try:
        result = await public_storage.load(payload_id)
    except PublicDataStorageError as err:
        raise web.HTTPError(reason=err.roll_up)

    return web.json_response({"result": result})


class SaveSettingsSchema(Schema):
    settings = fields.Dict(required=False)


@docs(
    tags=["Public Data Storage"],
    summary="Set and configure current PublicDataStorage",
    description="""
    Example of a correct schema:
    {
        "settings":
        {
            "local": {
                "no_configuration_needed": "yes-1234"
            },
            "data_vault": {
                "no_configuration_needed": "yes-1234"
            },
            "own_your_data": {
                "client_id": "test-1234",
                "client_secret": "test-1234",
                "grant_type": "client_credentials"
            }
        }
    }
    """,
)
@request_schema(SaveSettingsSchema())
async def set_settings(request: web.BaseRequest):
    context = request.app["request_context"]
    body = await request.json()
    settings: dict = body.get("settings", None)

    if settings == None:
        raise web.HTTPNotFound(reason="Settings schema is empty")

    for key in settings:
        public_storage: PublicDataStorage = await context.inject(
            PublicDataStorage, {"public_storage_type": key}
        )
        public_storage.settings.update(settings.get(key))
        print("(key, public_storage.settings): ", key, public_storage.settings)

    return web.json_response({"success": "settings_updated"})


@docs(
    tags=["Public Data Storage"],
    summary="Get all registered public storage types and show their configuration",
)
async def get_settings(request: web.BaseRequest):
    context = request.app["request_context"]
    registered_types = context.settings.get("public_storage_registered_types")
    active_storage_type = context.settings.get("public_storage_type")
    response_message = {}

    for key in registered_types:
        context.settings.set_value("public_storage_type", key)
        public_storage = await context.inject(PublicDataStorage)
        response_message.update({key: public_storage.settings})

    context.settings.set_value("public_storage_type", active_storage_type)

    return web.json_response(response_message)


@docs(
    tags=["Public Data Storage"],
    summary="Set a public data storage type by name",
    description="for example: 'local', get possible types by calling 'GET /pds' endpoint",
)
@request_schema(SetActiveStorageTypeSchema())
async def set_active_storage_type(request: web.BaseRequest):
    context = request.app["request_context"]
    body = await request.json()

    public_storage_type = body.get("type", None)

    check_if_storage_type_is_registered = context.settings.get_value(
        "public_storage_registered_types"
    ).get(public_storage_type)

    if check_if_storage_type_is_registered == None:
        raise web.HTTPNotFound(
            reason="Chosen type is not in the registered list, make sure there are no typos! Use GET settings to look for registered types"
        )

    context.settings.set_value("public_storage_type", public_storage_type)

    return web.json_response({"success_type_exists": public_storage_type})


@docs(
    tags=["Public Data Storage"],
    summary="Get all registered public storage types, get which storage_type is active",
)
async def get_storage_types(request: web.BaseRequest):
    context = request.app["request_context"]
    registered_types = context.settings.get("public_storage_registered_types")
    active_storage_type = context.settings.get("public_storage_type")

    registered_type_names = []
    for key in registered_types:
        registered_type_names.append(key)

    return web.json_response(
        {"active": active_storage_type, "types": registered_type_names}
    )


async def register(app: web.Application):
    """Register routes."""
    app.add_routes(
        [
            web.post("/pds/save", save_record),
            web.post("/pds/settings", set_settings),
            web.post("/pds/activate", set_active_storage_type),
            web.get(
                "/pds",
                get_storage_types,
                allow_head=False,
            ),
            web.get(
                "/pds/settings",
                get_settings,
                allow_head=False,
            ),
            web.get(
                "/pds/{payload_id}",
                get_record,
                allow_head=False,
            ),
        ]
    )