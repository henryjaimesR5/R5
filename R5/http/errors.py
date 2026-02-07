from typing import Optional


class HttpError(Exception):
    message = "Http error occurred"

    def __init__(self, custom_message: Optional[str] = None):
        msg = custom_message if custom_message else self.message
        super().__init__(msg)


class HttpDisabledException(HttpError):
    message = "Http client is disabled"


class HttpTimeoutError(HttpError):
    message = "Http request timed out"


class HttpConnectionError(HttpError):
    message = "Http connection error"


class HttpMappingError(HttpError):
    message = "Http Error mapping response to DTO"
