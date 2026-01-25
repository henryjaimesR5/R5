class HttpError(Exception):
    """Base exception para errores HTTP."""
    pass


class HttpTimeoutError(HttpError):
    """Error de timeout en request HTTP."""
    pass


class HttpConnectionError(HttpError):
    """Error de conexión HTTP."""
    pass


class HttpResponseError(HttpError):
    """Error en respuesta HTTP."""
    
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class HttpMappingError(HttpError):
    """Error al mapear respuesta a DTO."""
    pass
