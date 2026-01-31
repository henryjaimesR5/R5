class HttpError(Exception):
    message = "Http error ocurred "

    def __init__(self):
        super().__init__(self.message)


class HttpDisabledException(HttpError):
    message = "Http client is disabled"


class HttpTimeoutError(HttpError):
    message = "Http request timed out"


class HttpConnectionError(HttpError):
    message = "Http connection error"


class HttpMappingError(HttpError):
    message = "Http Error mapping response to DTO"
