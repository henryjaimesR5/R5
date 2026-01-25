# HTTP API Reference

Documentación completa de la API del módulo HTTP.

## Http Client

::: R5.http.http.Http
    options:
      show_source: true
      members:
        - __init__
        - __aenter__
        - __aexit__
        - get
        - post
        - put
        - patch
        - delete
        - retry
        - on_before
        - on_after
        - close

## HttpConfig

::: R5.http.http.HttpConfig
    options:
      show_source: true

## Result

::: R5.http.result.Result
    options:
      show_source: true
      members:
        - from_response
        - from_exception
        - on_status
        - on_exception
        - to

## Errores

### HttpError

::: R5.http.errors.HttpError
    options:
      show_source: true

### HttpTimeoutError

::: R5.http.errors.HttpTimeoutError
    options:
      show_source: true

### HttpConnectionError

::: R5.http.errors.HttpConnectionError
    options:
      show_source: true

### HttpResponseError

::: R5.http.errors.HttpResponseError
    options:
      show_source: true

### HttpMappingError

::: R5.http.errors.HttpMappingError
    options:
      show_source: true
