"""Credential exchange admin routes."""

from aiohttp_apispec import (
    docs,
    match_info_schema,
    querystring_schema,
    request_schema,
    response_schema,
)
from aiohttp import web
from marshmallow import fields
import logging
from ....messaging.models.base import OpenAPISchema
from .messages.credential_issue import CredentialIssue
from aries_cloudagent.protocols.issue_credential.v1_1.messages.credential_request import (
    CredentialRequest,
)
from .utils import (
    CredentialExchangeRecord,
    retrieve_credential_exchange,
    retrieve_connection,
    create_credential,
)
from aries_cloudagent.aathcf.credentials import raise_exception_invalid_state


LOG = logging.getLogger(__name__).info


class RequestCredentialSchema(OpenAPISchema):
    credential_values = fields.Dict()
    connection_id = fields.Str(required=True)


class IssueCredentialQuerySchema(OpenAPISchema):
    credential_exchange_id = fields.Str(required=False)


class RetrieveCredentialExchangeQuerySchema(OpenAPISchema):
    connection_id = fields.Str(required=False)
    thread_id = fields.Str(required=False)
    initiator = fields.Str(required=False)
    role = fields.Str(required=False)
    state = fields.Str(required=False)


@docs(tags=["issue-credential"], summary="Issue credential ")
@querystring_schema(IssueCredentialQuerySchema())
async def issue_credential(request: web.BaseRequest):
    context = request.app["request_context"]
    outbound_handler = request.app["outbound_message_router"]

    credential_exchange_id = request.query.get("credential_exchange_id")
    exchange = await retrieve_credential_exchange(context, credential_exchange_id)
    raise_exception_invalid_state(
        exchange,
        CredentialExchangeRecord.STATE_REQUEST_RECEIVED,
        CredentialExchangeRecord.ROLE_ISSUER,
        web.HTTPBadRequest,
    )
    connection = await retrieve_connection(context, exchange.connection_id)
    request = exchange.credential_request
    credential = await create_credential(context, request, connection, web.HTTPError)
    LOG("CREDENTIAL %s", credential)

    issue = CredentialIssue(credential=credential)
    issue.assign_thread_id(exchange.thread_id)
    await outbound_handler(issue, connection_id=connection.connection_id)

    exchange.state = CredentialExchangeRecord.STATE_ISSUED
    await exchange.save(context)

    return web.json_response(credential)


@docs(tags=["issue-credential"], summary="Request Credential")
@request_schema(RequestCredentialSchema())
async def request_credential(request: web.BaseRequest):
    context = request.app["request_context"]
    outbound_handler = request.app["outbound_message_router"]

    body = await request.json()
    credential_values = body.get("credential_values")
    connection_id = body.get("connection_id")
    connection_record = await retrieve_connection(context, connection_id)

    issue = CredentialRequest(credential={"credential_values": credential_values})
    await outbound_handler(issue, connection_id=connection_record.connection_id)

    exchange = CredentialExchangeRecord(
        connection_id=connection_id,
        thread_id=issue._thread_id,
        initiator=CredentialExchangeRecord.INITIATOR_SELF,
        role=CredentialExchangeRecord.ROLE_HOLDER,
        state=CredentialExchangeRecord.STATE_REQUEST_SENT,
        credential_request={"credential_values": credential_values},
    )

    exchange_id = await exchange.save(
        context, reason="Save record of agent credential exchange"
    )

    return web.json_response({"credential_exchange_id": exchange_id})


@docs(tags=["issue-credential"], summary="Retrieve Credential Exchange")
@querystring_schema(RetrieveCredentialExchangeQuerySchema())
async def retrieve_credential_exchange_endpoint(request: web.BaseRequest):
    context = request.app["request_context"]

    records = await CredentialExchangeRecord.query(context, tag_filter=request.query)

    result = []
    for i in records:
        result.append(i.serialize())

    return web.json_response(result)


async def register(app: web.Application):
    """Register routes."""

    app.add_routes(
        [
            web.post("/issue-credential/issue", issue_credential),
            web.post("/issue-credential/request", request_credential),
            web.get(
                "/issue-credential/exchange/record",
                retrieve_credential_exchange_endpoint,
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
            "name": "issue-credential",
            "description": "Credential issuance",
            # "externalDocs": {"description": "Specification", "url": SPEC_URI},
        }
    )
