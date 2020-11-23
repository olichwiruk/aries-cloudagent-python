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
from aries_cloudagent.aathcf.credentials import PresentationRequestedAttributesSchema
from .messages.request_proof import RequestProof
from .messages.present_proof import PresentProof
from .models.utils import retrieve_exchange
import uuid
import logging
import collections

LOG = logging.getLogger(__name__).info


class PresentationRequestAPISchema(OpenAPISchema):
    requested_attributes = fields.Dict(
        keys=fields.Str(),
        values=fields.Nested(PresentationRequestedAttributesSchema),
        required=True,
        many=True,
    )
    connection_id = fields.Str(required=True)


class PresentProofAPISchema(OpenAPISchema):
    exchange_record_id = fields.Str(required=True)
    requested_credentials = fields.Dict(
        keys=fields.Str(),
        values=fields.Dict(),
        required=True,
        many=True,
    )


@docs(tags=["present-proof"], summary="Sends a proof presentation")
@request_schema(PresentationRequestAPISchema())
async def request_presentation_api(request: web.BaseRequest):
    """
    Request handler for sending a presentation.

    Args:
        request: aiohttp request object

    Returns:
        The presentation exchange details

    """
    context = request.app["request_context"]
    outbound_handler = request.app["outbound_message_router"]
    body = await request.json()

    connection_id = body.get("connection_id")
    connection_record = await retrieve_connection(context, connection_id)

    type = body.get("type")
    context_field = body.get("context")
    requested_attributes = body.get("requested_attributes")

    presentation_request = {
        "nonce": str(uuid.uuid4()),
        "requested_attributes": requested_attributes,
    }

    message = RequestProof(presentation_request=presentation_request)
    await outbound_handler(message, connection_id=connection_id)

    exchange_record = THCFPresentationExchange(
        connection_id=connection_id,
        thread_id=message._thread_id,
        initiator=THCFPresentationExchange.INITIATOR_SELF,
        role=THCFPresentationExchange.ROLE_VERIFIER,
        state=THCFPresentationExchange.STATE_REQUEST_SENT,
        presentation_request=presentation_request,
    )

    LOG("exchange_record %s", exchange_record)
    await exchange_record.save(context)
    return web.json_response({"thread_id": exchange_record.thread_id})


@docs(tags=["present-proof"], summary="Send a credential presentation")
@request_schema(PresentProofAPISchema())
async def present_proof_api(request: web.BaseRequest):
    """
    Allows to respond to an already existing exchange with a proof presentation.

    Args:
        request: aiohttp request object

    Returns:
        The presentation exchange details

    """
    context = request.app["request_context"]
    outbound_handler = request.app["outbound_message_router"]

    body = await request.json()
    exchange_record_id = body.get("exchange_record_id")
    requested_credentials = body.get("requested_credentials")

    exchange_record = await retrieve_exchange(
        context, exchange_record_id, web.HTTPNotFound
    )

    if exchange_record.state != exchange_record.STATE_REQUEST_RECEIVED:
        raise web.HTTPBadRequest(
            reason="Invalid exchange state" + exchange_record.state
        )
    if exchange_record.role != exchange_record.ROLE_PROVER:
        raise web.HTTPBadRequest(
            reason="Invalid exchange state" + exchange_record.state
        )

    connection_record: ConnectionRecord = await retrieve_connection(
        context, exchange_record.connection_id
    )

    try:
        holder: BaseHolder = await context.inject(BaseHolder)
        requested_credentials = {"requested_attributes": requested_credentials}
        presentation = await holder.create_presentation(
            presentation_request=exchange_record.presentation_request,
            requested_credentials=requested_credentials,
            schemas={},
            credential_definitions={},
        )
    except HolderError as err:
        raise web.HTTPInternalServerError(reason=err.roll_up)

    message = PresentProof(credential_presentation=presentation)
    message.assign_thread_id(exchange_record.thread_id)
    await outbound_handler(message, connection_id=connection_record.connection_id)

    exchange_record.state = exchange_record.STATE_PRESENTATION_SENT
    exchange_record.presentation = json.loads(
        presentation, object_pairs_hook=collections.OrderedDict
    )
    await exchange_record.save(context)

    return web.json_response("success, proof sent and exchange updated")


class RetrieveExchangeQuerySchema(OpenAPISchema):
    connection_id = fields.Str(required=False)
    thread_id = fields.Str(required=False)
    initiator = fields.Str(required=False)
    role = fields.Str(required=False)
    state = fields.Str(required=False)


@docs(tags=["present-proof"], summary="retrieve exchange record")
@querystring_schema(RetrieveExchangeQuerySchema())
async def retrieve_credential_exchange_api(request: web.BaseRequest):
    context = request.app["request_context"]
    outbound_handler = request.app["outbound_message_router"]

    records = await THCFPresentationExchange.query(context, tag_filter=request.query)

    result = []
    for i in records:
        result.append(i.serialize())

    return web.json_response(result)


async def register(app: web.Application):
    """Register routes."""

    app.add_routes(
        [
            web.post(
                "/present-proof/request",
                request_presentation_api,
            ),
            web.post(
                "/present-proof/present",
                present_proof_api,
            ),
            web.get(
                "/present-proof/exchange/record",
                retrieve_credential_exchange_api,
                allow_head=False,
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
