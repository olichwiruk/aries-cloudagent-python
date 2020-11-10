"""Admin routes for presentations."""

import json

from aiohttp import web
from aiohttp_apispec import (
    docs,
    match_info_schema,
    querystring_schema,
    request_schema,
    response_schema,
)
from marshmallow import fields, validate, validates_schema
from marshmallow.exceptions import ValidationError

from ....connections.models.connection_record import ConnectionRecord
from ....holder.base import BaseHolder, HolderError
from ....indy.util import generate_pr_nonce
from .models.presentation_exchange import THCFPresentationExchange
from ....messaging.models.base import BaseModelError
from ....messaging.models.openapi import OpenAPISchema
from ....messaging.valid import (
    INT_EPOCH,
    NATURAL_NUM,
    UUIDFour,
    UUID4,
    WHOLE_NUM,
)
from ....storage.error import StorageError, StorageNotFoundError
from ....utils.tracing import trace_event, get_timer, AdminAPIMessageTracingSchema
from ....wallet.error import WalletNotFoundError
from ...problem_report.v1_0 import internal_error
from aries_cloudagent.protocols.issue_credential.v1_1.utils import retrieve_connection


class RequestedValueSchema(OpenAPISchema):
    value = fields.Str(required=True)
    issuer = fields.Str(required=False)


class PresentationRequestSchema(OpenAPISchema):
    requested_values = fields.Nested(RequestedValueSchema(), required=True)
    connection_id = fields.Str(required=True)


@docs(tags=["present-proof"], summary="Sends a proof presentation")
@request_schema(PresentationRequestSchema())
async def presentation_exchange_request_presentation(request: web.BaseRequest):
    """
    Request handler for sending a presentation.

    Args:
        request: aiohttp request object

    Returns:
        The presentation exchange details

    """
    context = request.app["request_context"]
    outbound_handler = request.app["outbound_message_router"]
    presentation_exchange_id = request.match_info["pres_ex_id"]

    body = await request.json()
    connection_id = body.get("connection_id")
    requested_values = body.get("requested_values")

    connection_record = await retrieve_connection(context, connection_id)

    # "self_attested_attributes": body.get("self_attested_attributes"),
    # "requested_attributes": body.get("requested_attributes"),
    # "requested_predicates": body.get("requested_predicates"),

    # await outbound_handler(presentation_message, connection_id=connection_id)

    return web.json_response(requested_values)


async def register(app: web.Application):
    """Register routes."""

    app.add_routes(
        [
            web.post(
                "/present-proof/records/{pres_ex_id}/send-presentation",
                presentation_exchange_send_presentation,
            ),
        ]
    )


def post_process_routes(app: web.Application):
    """Amend swagger API."""

    # Add top-level tags description
    if "tags" not in app._state["swagger_dict"]:
        app._state["swagger_dict"]["tags"] = []
    app._state["swagger_dict"]["tags"].append(
        {
            "name": "present-proof",
            "description": "Proof presentation",
            "externalDocs": {"description": "Specification"},
        }
    )
