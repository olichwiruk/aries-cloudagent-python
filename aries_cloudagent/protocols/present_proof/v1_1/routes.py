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
from ....messaging.models.openapi import OpenAPISchema
from aries_cloudagent.protocols.issue_credential.v1_1.utils import retrieve_connection
from aries_cloudagent.aathcf.credentials import (
    raise_exception_invalid_state,
)
from .messages.request_proof import RequestProof
from .messages.present_proof import PresentProof
from .models.utils import retrieve_exchange
import logging
import collections
from aries_cloudagent.pdstorage_thcf.api import load_multiple
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

    # raise web.HTTPBadRequest()
    raise_exception_invalid_state(
        exchange_record,
        THCFPresentationExchange.STATE_PRESENTATION_RECEIVED,
        THCFPresentationExchange.ROLE_VERIFIER,
        web.HTTPBadRequest,
    )

    connection_record: ConnectionRecord = await retrieve_connection(
        context, exchange_record.connection_id
    )

    print("STATUS:", str(query.get("status")))
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


@docs(tags=["PersonalDataStorage"])
async def debug_endpoint(request: web.BaseRequest):
    context = request.app["request_context"]
    record = THCFPresentationExchange()
    await record.set_ack_cred(context, OrderedDict({"data": "abc"}))
    # await record.store_presentation(context, OrderedDict({"data": "abc"}))
    response = await record.get_ack_cred(context)
    print(response)
    # response = await record.get_presentation(context)
    # print(response)


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
