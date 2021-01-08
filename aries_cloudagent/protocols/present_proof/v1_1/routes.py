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
from marshmallow import fields
from ....connections.models.connection_record import ConnectionRecord
from ....holder.base import BaseHolder, HolderError
from .models.presentation_exchange import THCFPresentationExchange
from ....messaging.models.openapi import OpenAPISchema, Schema
from aries_cloudagent.protocols.issue_credential.v1_1.utils import retrieve_connection
from aries_cloudagent.aathcf.credentials import (
    raise_exception_invalid_state,
)
from .messages.request_proof import RequestProof
from .messages.present_proof import PresentProof
from .models.utils import retrieve_exchange
import logging
import collections
from aries_cloudagent.pdstorage_thcf.api import (
    load_multiple,
    pds_load,
    pds_save,
    pds_save_a,
)
from aries_cloudagent.holder.pds import CREDENTIALS_TABLE
from aries_cloudagent.pdstorage_thcf.error import PDSError
from ...issue_credential.v1_1.utils import create_credential
from aries_cloudagent.protocols.issue_credential.v1_1.routes import (
    routes_get_public_did,
)

LOG = logging.getLogger(__name__).info

from .messages.acknowledge_proof import AcknowledgeProof
from collections import OrderedDict


class PresentationRequestAPISchema(OpenAPISchema):
    connection_id = fields.Str(required=True)
    requested_attributes = fields.List(fields.Str(required=True), required=True)
    issuer_did = fields.Str(required=False)
    schema_base_dri = fields.Str(required=True)


class PresentProofAPISchema(OpenAPISchema):
    exchange_record_id = fields.Str(required=True)
    credential_id = fields.Str(required=True)


class RetrieveExchangeQuerySchema(OpenAPISchema):
    connection_id = fields.Str(required=False)
    thread_id = fields.Str(required=False)
    initiator = fields.Str(required=False)
    role = fields.Str(required=False)
    state = fields.Str(required=False)


class AcknowledgeProofSchema(OpenAPISchema):
    exchange_record_id = fields.Str(required=True)
    status = fields.Boolean(required=True)


@docs(tags=["present-proof"], summary="Sends a proof presentation")
@request_schema(PresentationRequestAPISchema())
async def request_presentation_api(request: web.BaseRequest):
    """Request handler for sending a presentation."""
    context = request.app["request_context"]
    outbound_handler = request.app["outbound_message_router"]
    body = await request.json()

    connection_id = body.get("connection_id")
    await retrieve_connection(context, connection_id)  # throw exception if not found

    presentation_request = {
        "requested_attributes": body.get("requested_attributes"),
        "schema_base_dri": body.get("schema_base_dri"),
    }
    issuer_did = body.get("issuer_did")
    if issuer_did is not None:
        presentation_request["issuer_did"] = issuer_did

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

    return web.json_response(
        {
            "success": True,
            "message": "proof sent and exchange updated",
            "exchange_id": exchange_record._id,
            "thread_id": message._thread_id,
            "connection_id": connection_id,
        }
    )


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
    credential_id = body.get("credential_id")

    exchange_record = await retrieve_exchange(
        context, exchange_record_id, web.HTTPNotFound
    )

    raise_exception_invalid_state(
        exchange_record,
        THCFPresentationExchange.STATE_REQUEST_RECEIVED,
        THCFPresentationExchange.ROLE_PROVER,
        web.HTTPBadRequest,
    )

    connection_record: ConnectionRecord = await retrieve_connection(
        context, exchange_record.connection_id
    )

    try:
        holder: BaseHolder = await context.inject(BaseHolder)
        requested_credentials = {"credential_id": credential_id}
        presentation = await holder.create_presentation(
            presentation_request=exchange_record.presentation_request,
            requested_credentials=requested_credentials,
            schemas={},
            credential_definitions={},
        )
    except HolderError as err:
        raise web.HTTPInternalServerError(reason=err.roll_up)

    public_did = await routes_get_public_did(context)
    message = PresentProof(
        credential_presentation=presentation, prover_public_did=public_did
    )
    message.assign_thread_id(exchange_record.thread_id)
    await outbound_handler(message, connection_id=connection_record.connection_id)

    exchange_record.state = exchange_record.STATE_PRESENTATION_SENT
    exchange_record.presentation = json.loads(
        presentation, object_pairs_hook=collections.OrderedDict
    )
    await exchange_record.save(context)

    return web.json_response(
        {
            "success": True,
            "message": "proof sent and exchange updated",
            "exchange_id": exchange_record._id,
        }
    )


@docs(tags=["present-proof"], summary="retrieve exchange record")
@querystring_schema(AcknowledgeProofSchema())
async def acknowledge_proof(request: web.BaseRequest):
    context = request.app["request_context"]
    outbound_handler = request.app["outbound_message_router"]
    query = request.query

    exchange_record: THCFPresentationExchange = await retrieve_exchange(
        context, query.get("exchange_record_id"), web.HTTPNotFound
    )

    raise_exception_invalid_state(
        exchange_record,
        THCFPresentationExchange.STATE_PRESENTATION_RECEIVED,
        THCFPresentationExchange.ROLE_VERIFIER,
        web.HTTPBadRequest,
    )

    connection_record: ConnectionRecord = await retrieve_connection(
        context, exchange_record.connection_id
    )

    credential = await create_credential(
        context,
        {
            "credential_type": "ProofAcknowledgment",
            "credential_values": {
                "status": str(query.get("status")),
            },
        },
        their_public_did=exchange_record.prover_public_did,
        exception=web.HTTPInternalServerError,
    )

    message = AcknowledgeProof(credential=credential)
    message.assign_thread_id(exchange_record.thread_id)
    await outbound_handler(message, connection_id=connection_record.connection_id)

    exchange_record.acknowledgment_credential = json.loads(
        credential, object_pairs_hook=OrderedDict
    )
    exchange_record.state = exchange_record.STATE_ACKNOWLEDGED
    await exchange_record.save(context)
    return web.json_response(
        {
            "success": True,
            "message": "ack sent and exchange record updated",
            "exchange_record_id": exchange_record._id,
        }
    )


class DebugEndpointSchema(OpenAPISchema):
    # {DRI1: [{timestamp: 23423453453534, data: {...}},{}], DRI2: [{},{}], DRI3: [{},{}] }
    #     {d: {456...}, t: Date.current.getMilliseconds()} } d - data; t - timestamp
    oca_data = fields.Dict()


# TODO: Delete DRI: When saving
async def pds_oca_data_format_save(context, data):
    ids_of_saved_schemas = {}
    for oca_schema_base_dri in data:
        if oca_schema_base_dri.startswith("DRI:"):
            payload_id = await pds_save_a(
                context,
                data[oca_schema_base_dri],
                oca_schema_dri=oca_schema_base_dri,
            )
            ids_of_saved_schemas[oca_schema_base_dri] = payload_id
        else:
            ids_of_saved_schemas[
                oca_schema_base_dri
            ] = "Invalid format, DRIs should start with 'DRI:'"

    return ids_of_saved_schemas


async def pds_oca_data_format_serialize_item_recursive(context, key, val):
    new_val = val
    if isinstance(val, dict):
        new_val = await pds_oca_data_format_serialize_dict_recursive(context, val)
    elif val.startswith("DRI:"):
        new_val = await pds_load(context, val)
        new_val = await pds_oca_data_format_serialize_dict_recursive(context, new_val)
    return new_val


async def pds_oca_data_format_serialize_dict_recursive(context, dct):
    new_dict = {}
    for k, v in dct.items():
        new_dict[k] = await pds_oca_data_format_serialize_item_recursive(context, k, v)

    return new_dict


@docs(tags=["PersonalDataStorage"])
@request_schema(DebugEndpointSchema)
async def debug_endpoint(request: web.BaseRequest):
    context = request.app["request_context"]

    data = {"data": "data"}
    payload_id = await pds_save_a(context, data, oca_schema_dri="12345", table="test")
    ret = await pds_load(context, payload_id)
    assert ret == data

    # body = await request.json()
    # oca_data = body["oca_data"]
    # print(oca_data)

    data = {
        "DRI:12345": {"t": "o", "p": {"address": "DRI:123456", "test_value": "ok"}},
        "DRI:123456": {
            "t": "o",
            "p": {"second_dri": "DRI:1234567", "test_value": "ok"},
        },
        "DRI:1234567": {"t": "o", "p": {"third_dri": "DRI:123456", "test_value": "ok"}},
        "1234567": {"t": "o", "p": {"third_dri": "DRI:123456", "test_value": "ok"}},
    }

    ids = await pds_oca_data_format_save(context, data)
    serialized = await pds_oca_data_format_serialize_dict_recursive(context, data)

    return web.json_response({"success": True, "result": ids, "serialized": serialized})


@docs(tags=["present-proof"], summary="retrieve exchange record")
@querystring_schema(RetrieveExchangeQuerySchema())
async def retrieve_credential_exchange_api(request: web.BaseRequest):
    context = request.app["request_context"]

    records = await THCFPresentationExchange.query(context, tag_filter=request.query)

    result = []
    for i in records:
        result.append(i.serialize())

    """
    Download credentials
    """

    try:
        credentials = await load_multiple(context, table=CREDENTIALS_TABLE)
        credentials = json.loads(credentials)
    except json.JSONDecodeError:
        LOG(
            "Error parsing credentials, perhaps there are no credentials in store %s",
            credentials,
        )
        credentials = {}
    except PDSError as err:
        LOG("PDSError %s", err.roll_up)
        credentials = {}

    """
    DEBUG VERSION
    for rec in result:
        rec["list_of_matching_credentials"] = []
        for cred in credentials:
            cred = json.loads(cred)
            cred_content = json.loads(cred["content"])
            i_have_credential = True
            for attr in rec["presentation_request"]["requested_attributes"]:
                if attr not in cred_content["credentialSubject"]:
                    i_have_credential = False

            if i_have_credential is True:
                rec["list_of_matching_credentials"].append(cred["dri"])
    """

    """
    Match the credential requests with credentials in the possesion of the agent
    in this case we check if both issuer_did and oca_schema_dri are correct

    TODO: Optimization, create a dictionary of credential - schema base matches,
    with schema base as key
    """

    for rec in result:
        rec["list_of_matching_credentials"] = []
        for cred in credentials:
            cred_content = json.loads(cred["content"])

            print("Cred content:", cred_content)

            record_base_dri = rec["presentation_request"].get(
                "schema_base_dri", "INVALIDA"
            )
            # record_issuer_did = rec["presentation_request"].get(
            #     "issuer_did", "INVALIDB"
            # )
            cred_base_dri = cred_content["credentialSubject"].get(
                "oca_schema_dri", "INVALIDC"
            )
            # cred_issuer_did = cred_content["credentialSubject"].get(
            #     "issuer_did", "INVALIDD"
            # )

            if (
                record_base_dri
                == cred_base_dri
                # and record_issuer_did == cred_issuer_did
            ):
                rec["list_of_matching_credentials"].append(cred["dri"])

    return web.json_response({"success": True, "result": result})


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
            web.post(
                "/present-proof/acknowledge",
                acknowledge_proof,
            ),
            web.get(
                "/present-proof/exchange/record",
                retrieve_credential_exchange_api,
                allow_head=False,
            ),
            web.post("/present-proof/debug", debug_endpoint),
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
