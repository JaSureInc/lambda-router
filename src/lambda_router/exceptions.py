class ConfigError(ValueError):
    """
    A problem applying the config template has occured.
    """


class HandledError(Exception):
    """
    An exepected error that needs to be raised in the lambda runtime but
    should not be sent to the configured exception handlers.
    """
