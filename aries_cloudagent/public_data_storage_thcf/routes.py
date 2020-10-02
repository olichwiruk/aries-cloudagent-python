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


class SaveRecordSchema(Schema):
    payload = fields.Str(required=False)


@docs(tags=["public_data_storage"], summary="Save data in a public data storage")
@request_schema(SaveRecordSchema())
async def save_record(request: web.BaseRequest):
    context = request.app["request_context"]
    body = await request.json()

    payload = body.get("payload", None)
    assert payload != None
    print("payload: ", payload)

    public_storage: PublicDataStorage = await context.inject(PublicDataStorage)
    payload_id = await public_storage.save(payload)

    return web.json_response({"payload_id": payload_id})


@docs(
    tags=["public_data_storage"],
    summary="Retrieve data from a public data storage using data id",
)
async def get_record(request: web.BaseRequest):
    context = request.app["request_context"]
    payload_id = request.match_info["payload_id"]

    assert payload_id != None

    public_storage: PublicDataStorage = await context.inject(PublicDataStorage)
    result = await public_storage.read(payload_id)

    return web.json_response({"result": result})


class SaveRecordSchema(Schema):
    public_storage_type = fields.Str(required=False)
    settings = fields.Dict(required=False)


@docs(
    tags=["public_data_storage"],
    summary="Set and configure current PublicDataStorage",
)
@request_schema(SaveRecordSchema())
async def configure(request: web.BaseRequest):
    context = request.app["request_context"]
    body = await request.json()

    public_storage_type = body.get("public_storage_type", None)
    settings = body.get("settings", None)
    response_message = {}

    # TODO: Check whether correct
    if public_storage_type != None:
        context.settings.set_value("public_storage_type", public_storage_type)

        response_message.update({"public_storage_type set to": public_storage_type})

    if settings != None:
        public_storage: PublicDataStorage = await context.inject(PublicDataStorage)
        public_storage.settings = settings

        response_message.update({"settings set to": settings})

    return web.json_response(response_message)


@docs(
    tags=["public_data_storage"],
    summary="Retrieve data from a public data storage using data id",
)
async def DEBUGget_all(request: web.BaseRequest):
    context = request.app["request_context"]
    payload_id = request.match_info["payload_id"]

    assert payload_id != None

    public_storage: PublicDataStorage = await context.inject(PublicDataStorage)
    result = await public_storage.read_all()

    return web.json_response({"result": result})


async def register(app: web.Application):
    """Register routes."""
    app.add_routes(
        [
            web.post("/pbs/save", save_record),
            web.post("/pbs/configure", configure),
            web.get(
                "/pbs/{payload_id}",
                get_record,
                allow_head=False,
            ),
            web.get(
                "/pbs/debug",
                DEBUGget_all,
                allow_head=False,
            ),
        ]
    )