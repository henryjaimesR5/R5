from typing import Any, Callable, Optional

from anyio import sleep
import httpx

from R5.http.errors import HttpConnectionError, HttpDisabledException, HttpTimeoutError
from R5.http.result import Result
from R5.ioc import config, inject, resource


@config(file="application.yml", required=False)
class HttpConfig:
    http_enable: bool = True
    http_max_connections: int = 100
    http_max_keepalive_connections: int = 20
    http_keepalive_expiry: float = 5.0
    http_connect_timeout: float = 5.0
    http_read_timeout: float = 30.0
    http_write_timeout: float = 30.0
    http_pool_timeout: float = 5.0
    http_default_headers: dict[str, str] = {}
    http_user_agent: str = "R5-HTTP/1.0"
    http_follow_redirects: bool = True
    http_retry_delay: float = 1.0
    http_retry_backoff: float = 2.0


@resource
class Http:
    """Cliente HTTP asíncrono con pooling, retry y proxy rotation.

    Uso:
        @inject
        async def my_service(http: Http):
            result = await http.get("/users/1")
            user = result.to(UserDTO)

        Retry:
            http.retry(3, delay=1.0, when_status=(503,)).get(url)

        Proxy:
            http.proxy("http://proxy:8080").get(url)
            http.proxy(["http://p1:8080", "http://p2:8080"]).get(url)

        Chaining:
            http.proxy(proxies).retry(3).on_before(handler).get(url)

        Result:
            user = await http.get("/users/1").to(UserDTO)
    """

    @inject
    def __init__(self, config: HttpConfig):
        self._config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._before_handlers: list[Callable[[httpx.Request], None]] = []
        self._after_handlers: list[Callable[[httpx.Request, httpx.Response], None]] = []
        self._retry_attempts: Optional[int] = None
        self._retry_delay: float = config.http_retry_delay
        self._retry_backoff: float = config.http_retry_backoff
        self._retry_when_status: Optional[tuple[int, ...]] = None
        self._retry_when_exception: Optional[tuple[type[Exception], ...]] = None
        self._proxy_list: list[str] = []
        self._proxy_index: int = 0
        self._proxy_rotate_on_status: Optional[tuple[int, ...]] = None
        self._proxy_rotate_on_exception: Optional[tuple[type[Exception], ...]] = None

    async def __aenter__(self) -> "Http":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def _build_client_config(self) -> tuple[httpx.Limits, httpx.Timeout, dict]:
        limits = httpx.Limits(
            max_connections=self._config.http_max_connections,
            max_keepalive_connections=self._config.http_max_keepalive_connections,
            keepalive_expiry=self._config.http_keepalive_expiry,
        )
        timeout = httpx.Timeout(
            connect=self._config.http_connect_timeout,
            read=self._config.http_read_timeout,
            write=self._config.http_write_timeout,
            pool=self._config.http_pool_timeout,
        )
        headers = {
            "User-Agent": self._config.http_user_agent,
            **self._config.http_default_headers,
        }
        return limits, timeout, headers

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            limits, timeout, headers = self._build_client_config()
            self._client = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                headers=headers,
                follow_redirects=self._config.http_follow_redirects,
            )
        return self._client

    def _create_proxy_client(self, proxy: str) -> httpx.AsyncClient:
        limits, timeout, headers = self._build_client_config()
        return httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            headers=headers,
            follow_redirects=self._config.http_follow_redirects,
            proxy=proxy,
        )

    def on_before(self, handler: Callable[[httpx.Request], None]) -> "Http":
        self._before_handlers.append(handler)
        return self

    def on_after(
        self, handler: Callable[[httpx.Request, httpx.Response], None]
    ) -> "Http":
        self._after_handlers.append(handler)
        return self

    def retry(
        self,
        attempts: int,
        delay: float = 1.0,
        backoff: float = 2.0,
        when_status: Optional[tuple[int, ...]] = None,
        when_exception: Optional[tuple[type[Exception], ...]] = None,
    ) -> "Http":
        self._retry_attempts = attempts
        self._retry_delay = delay
        self._retry_backoff = backoff
        self._retry_when_status = when_status
        self._retry_when_exception = when_exception
        return self

    def proxy(
        self,
        proxies: str | list[str],
        rotate_on_status: Optional[tuple[int, ...]] = None,
        rotate_on_exception: Optional[tuple[type[Exception], ...]] = None,
    ) -> "Http":
        self._proxy_list = [proxies] if isinstance(proxies, str) else proxies
        self._proxy_index = 0
        self._proxy_rotate_on_status = rotate_on_status
        self._proxy_rotate_on_exception = rotate_on_exception
        return self

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        data: Optional[Any] = None,
        content: Optional[bytes] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: Optional[float] = None,
        follow_redirects: Optional[bool] = None,
        on_before: Optional[Callable[[httpx.Request], None]] = None,
        on_after: Optional[Callable[[httpx.Request, httpx.Response], None]] = None,
        on_status: Optional[dict[int, Callable[[], None]]] = None,
        on_exception: Optional[Callable[[Exception], None]] = None,
        **kwargs: Any,
    ) -> Result:
        return await self._request(
            method,
            url,
            params=params,
            json=json,
            data=data,
            content=content,
            headers=headers,
            timeout=timeout,
            follow_redirects=follow_redirects,
            on_before=on_before,
            on_after=on_after,
            on_status=on_status,
            on_exception=on_exception,
            **kwargs,
        )

    async def _request(
        self,
        method: str,
        url: str,
        timeout: Optional[float] = None,
        follow_redirects: Optional[bool] = None,
        on_before: Optional[Callable[[httpx.Request], None]] = None,
        on_after: Optional[Callable[[httpx.Request, httpx.Response], None]] = None,
        on_status: Optional[dict[int, Callable[[], None]]] = None,
        on_exception: Optional[Callable[[Exception], None]] = None,
        **kwargs: Any,
    ) -> Result:
        if not self._config.http_enable:
            raise HttpDisabledException

        retry_attempts = self._retry_attempts or 0
        current_delay = self._retry_delay
        result: Optional[Result] = None
        proxy_client: Optional[httpx.AsyncClient] = None

        try:
            for attempt in range(retry_attempts + 1):
                try:
                    client = await self._get_client(proxy_client)
                    if self._proxy_list and proxy_client is None:
                        proxy_client = client

                    request_kwargs = kwargs.copy()
                    if timeout is not None:
                        request_kwargs["timeout"] = timeout

                    send_kwargs = {}
                    if follow_redirects is not None:
                        send_kwargs["follow_redirects"] = follow_redirects

                    request = client.build_request(method, url, **request_kwargs)

                    for handler in self._before_handlers:
                        handler(request)
                    if on_before:
                        on_before(request)

                    response = await client.send(request, **send_kwargs)

                    for handler in self._after_handlers:
                        handler(request, response)
                    if on_after:
                        on_after(request, response)

                    result = Result.from_response(response)

                    if on_status and result.status in on_status:
                        on_status[result.status]()

                    if self._should_rotate_on_status(result.status):
                        proxy_client = await self._rotate_proxy(proxy_client)

                    if self._should_retry_on_status(
                        result.status, attempt, retry_attempts
                    ):
                        await sleep(current_delay)
                        current_delay *= self._retry_backoff
                        continue

                    return result

                except Exception as e:
                    result = self._handle_exception(e, on_exception)

                    if self._should_rotate_on_exception(e):
                        proxy_client = await self._rotate_proxy(proxy_client)

                    if self._should_retry_on_exception(e, attempt, retry_attempts):
                        await sleep(current_delay)
                        current_delay *= self._retry_backoff
                        continue

                    return result

            return result or Result.from_exception(
                Exception("All attempts failed"), None
            )

        finally:
            if proxy_client and not proxy_client.is_closed:
                await proxy_client.aclose()
            self._clear_config()

    def _handle_exception(
        self, e: Exception, on_exception: Optional[Callable[[Exception], None]]
    ) -> Result:
        response = getattr(e, "response", None)

        if isinstance(e, httpx.TimeoutException):
            error = HttpTimeoutError()
        elif isinstance(e, httpx.ConnectError):
            error = HttpConnectionError()
        else:
            error = e

        result = Result.from_exception(error, response)

        if on_exception:
            on_exception(e)

        return result

    async def _get_client(
        self, current_proxy_client: Optional[httpx.AsyncClient]
    ) -> httpx.AsyncClient:
        if self._proxy_list:
            if current_proxy_client and not current_proxy_client.is_closed:
                return current_proxy_client
            return self._create_proxy_client(self._proxy_list[self._proxy_index])
        return await self._ensure_client()

    def _should_rotate_on_status(self, status: int) -> bool:
        return bool(
            self._proxy_list
            and self._proxy_rotate_on_status
            and status in self._proxy_rotate_on_status
        )

    def _should_rotate_on_exception(self, e: Exception) -> bool:
        return bool(
            self._proxy_list
            and self._proxy_rotate_on_exception
            and isinstance(e, self._proxy_rotate_on_exception)
        )

    async def _rotate_proxy(
        self, current_client: Optional[httpx.AsyncClient]
    ) -> Optional[httpx.AsyncClient]:
        if current_client and not current_client.is_closed:
            await current_client.aclose()
        if self._proxy_list:
            self._proxy_index = (self._proxy_index + 1) % len(self._proxy_list)
            return self._create_proxy_client(self._proxy_list[self._proxy_index])
        return None

    def _should_retry_on_status(
        self, status: int, attempt: int, max_attempts: int
    ) -> bool:
        return bool(
            self._retry_when_status
            and status in self._retry_when_status
            and attempt < max_attempts
        )

    def _should_retry_on_exception(
        self, e: Exception, attempt: int, max_attempts: int
    ) -> bool:
        if attempt >= max_attempts:
            return False
        if self._retry_when_exception:
            return isinstance(e, self._retry_when_exception)
        return self._retry_attempts is not None

    def _clear_config(self) -> None:
        self._retry_attempts = None
        self._retry_delay = self._config.http_retry_delay
        self._retry_backoff = self._config.http_retry_backoff
        self._retry_when_status = None
        self._retry_when_exception = None
        self._proxy_list = []
        self._proxy_index = 0
        self._proxy_rotate_on_status = None
        self._proxy_rotate_on_exception = None

    async def get(self, url: str, **kwargs: Any) -> Result:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> Result:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> Result:
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> Result:
        return await self.request("DELETE", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> Result:
        return await self.request("PATCH", url, **kwargs)

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
