from .base import *
from .error import *
from .message_types import *
from aries_cloudagent.messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    RequestContext,
)
from ..protocols.problem_report.v1_0.message import (
    ProblemReport,
)


class ExchangeDataAHandler(BaseHandler):
    """
    Stage first, this fires for the agent2, receive request to send data
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        print("ExchangeDataAHandler")
        assert isinstance(context.message, ExchangeDataA)
        pds: BasePersonalDataStorage = await context.inject(BasePersonalDataStorage)
        payload_dri = context.message.payload_dri

        try:
            payload = await pds.load(payload_dri)
            if payload == None:
                raise PersonalDataStorageNotFoundError
        except PersonalDataStorageError as err:
            print("TODO: ExchangeDataAHandler ProblemReport")
            return

        response = ExchangeDataB(payload=payload, payload_dri=payload_dri)
        response.assign_thread_from(context.message)
        await responder.send_reply(response)


class ExchangeDataBHandler(BaseHandler):
    """
    Stage second, this fires for the agent1, the initiator
    """

    async def handle(self, context: RequestContext, responder: BaseResponder):
        print("ExchangeDataBHandler")
        assert isinstance(context.message, ExchangeDataB)
        pds: BasePersonalDataStorage = await context.inject(BasePersonalDataStorage)

        try:
            payload_dri = await pds.save(context.message.payload)
        except PersonalDataStorageError as err:
            raise err.roll_up

        print("payload saved payload_dri:", payload_dri)
        if context.message.payload_dri:
            assert context.message.payload_dri == payload_dri