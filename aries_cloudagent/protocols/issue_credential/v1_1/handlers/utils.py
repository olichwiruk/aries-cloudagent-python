from .....messaging.base_handler import HandlerException


def debug_handler(log, context, MessageClass, handler_name_string):
    """
    log - logging function
    """
    log("%s called with context %s", handler_name_string, context)
    assert isinstance(context.message, MessageClass)
    log(
        "Received %s: %s",
        handler_name_string,
        context.message.serialize(as_string=True),
    )
    if not context.connection_ready:
        raise HandlerException("No connection established for " + handler_name_string)