class StatusCodeExceptions(Exception):
    """Exception for response != 200 statuses."""

    pass


class UnknownHomeWorkStatus(Exception):
    """Exception for unknown homework."""

    pass


class RequestConnectionError(Exception):
    """Exception for request and connection."""

    pass
