from typing import Optional, Any, Callable
from itertools import cycle
import httpx

from R5.ioc import resource, inject, config
from R5.http.result import Result
from R5.http.errors import HttpDisabledException


@config(file='application.yml', required=False)
class HttpConfig:
    """Configuración para el cliente HTTP.
    
    Attributes:
        max_connections: Máximo de conexiones en el pool
        max_keepalive_connections: Máximo de conexiones keep-alive
        keepalive_expiry: Tiempo de expiración de keep-alive en segundos
        connect_timeout: Timeout de conexión en segundos
        read_timeout: Timeout de lectura en segundos
        write_timeout: Timeout de escritura en segundos
        pool_timeout: Timeout del pool en segundos
        max_retries: Número máximo de reintentos
        retry_backoff_factor: Factor de backoff para reintentos
        retry_statuses: Lista de status codes que disparan retry
        proxies: Lista de proxies para rotación
        proxy_rotation: Si debe rotar entre proxies
        default_headers: Headers por defecto para todas las requests
        user_agent: User-Agent por defecto
        follow_redirects: Si debe seguir redirecciones por defecto
    """
    http_enable: bool = True
    http_max_connections: int = 100
    http_max_keepalive_connections: int = 20
    http_keepalive_expiry: float = 5.0
    
    http_connect_timeout: float = 5.0
    http_read_timeout: float = 30.0
    http_write_timeout: float = 30.0
    http_pool_timeout: float = 5.0
    
    http_max_retries: int = 3
    http_retry_backoff_factor: float = 0.5
    http_retry_statuses: list[int] = [429, 500, 502, 503, 504]
    
    http_proxies: list[str] = []
    http_proxy_rotation: bool = True
    
    http_default_headers: dict[str, str] = {}
    http_user_agent: str = "R5-HttpClient/1.0"
    http_follow_redirects: bool = True


@resource
class Http:
    """Cliente HTTP unificado con pool y proxy rotation.
    
    Singleton que gestiona:
    - Connection pooling con httpx.AsyncClient
    - Proxy rotation con round-robin
    - Configuración centralizada
    - Result pattern para manejo de errores
    
    Uso:
        @inject
        async def my_service(http: Http):
            result = await http.get("/users/1")
            user = result.to(UserDTO)
    """
    
    @inject
    def __init__(self, config: HttpConfig):
        """Inicializa Http client.
        
        Args:
            config: Configuración HTTP inyectada por IoC
        """
        self._config = config
        self._client: Optional[httpx.AsyncClient] = None
        
        self._proxies = config.http_proxies
        self._proxy_cycle = cycle(config.http_proxies) if config.http_proxies else None
        
        self._before_handlers: list[Callable[[httpx.Request], None]] = []
        self._after_handlers: list[Callable[[httpx.Request, httpx.Response], None]] = []
        
        self._retry_attempts: Optional[int] = None
        self._retry_delay: float = 1.0
        self._retry_backoff: float = 2.0
        self._retry_when_status: Optional[tuple[int, ...]] = None
        self._retry_when_exception: Optional[tuple[type[Exception], ...]] = None
    
    async def __aenter__(self) -> 'Http':
        """Async context manager entry.
        
        Llamado automáticamente por el resource provider.
        """
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit.
        
        Cierra automáticamente el cliente HTTP cuando el resource
        sale del scope (al finalizar la aplicación o request).
        """
        print("Closing Http client...")
        await self.close()
    
    async def _ensure_client(self) -> httpx.AsyncClient:
        """Crea o retorna cliente httpx con pool configurado.
        
        Lazy initialization del cliente HTTP para evitar crear
        conexiones hasta que sea necesario.
        
        Returns:
            Cliente httpx configurado con pool y timeouts
        """
        if self._client is None:
            limits = httpx.Limits(
                max_connections=self._config.http_max_connections,
                max_keepalive_connections=self._config.http_max_keepalive_connections,
                keepalive_expiry=self._config.http_keepalive_expiry
            )
            
            timeout = httpx.Timeout(
                connect=self._config.http_connect_timeout,
                read=self._config.http_read_timeout,
                write=self._config.http_write_timeout,
                pool=self._config.http_pool_timeout
            )
            
            default_headers = {
                "User-Agent": self._config.http_user_agent,
                **self._config.http_default_headers
            }
            
            self._client = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                headers=default_headers,
                follow_redirects=self._config.http_follow_redirects
            )
        
        return self._client
    
    def _get_proxy(self) -> Optional[str]:
        """Obtiene siguiente proxy en rotación.
        
        Usa itertools.cycle para round-robin infinito.
        Thread-safe ya que next() es atómico.
        
        Returns:
            URL del proxy o None si no hay proxies configurados
        """
        if self._proxy_cycle:
            return next(self._proxy_cycle)
        return None
    
    def on_before(self, handler: Callable[[httpx.Request], None]) -> 'Http':
        """Registra handler que se ejecuta ANTES de cada request.
        
        El handler recibe el httpx.Request antes de enviarlo.
        Útil para logging, modificación de headers, métricas, etc.
        
        Args:
            handler: Función que recibe httpx.Request
        
        Returns:
            self para permitir chaining
        
        Ejemplo:
            http.on_before(lambda req: print(f"→ {req.method} {req.url}"))
            result = await http.get("/users")  # Ejecuta handler automáticamente
        """
        self._before_handlers.append(handler)
        return self
    
    def on_after(self, handler: Callable[[httpx.Request, httpx.Response], None]) -> 'Http':
        """Registra handler que se ejecuta DESPUÉS de cada request exitosa.
        
        El handler recibe el httpx.Request y httpx.Response.
        Útil para logging, métricas, validaciones, etc.
        
        Args:
            handler: Función que recibe (request, response)
        
        Returns:
            self para permitir chaining
        
        Ejemplo:
            http.on_after(lambda req, res: print(f"← {res.status_code}"))
            result = await http.get("/users")  # Ejecuta handler automáticamente
        """
        self._after_handlers.append(handler)
        return self
    
    def retry(
        self,
        attempts: int,
        delay: float = 1.0,
        backoff: float = 2.0,
        when_status: Optional[tuple[int, ...]] = None,
        when_exception: Optional[tuple[type[Exception], ...]] = None
    ) -> 'Http':
        """Configura política de retry para la siguiente request.
        
        Patrón builder que permite encadenar configuración antes de .get()/.post().
        
        Args:
            attempts: Número de reintentos
            delay: Delay inicial en segundos
            backoff: Factor de backoff exponencial
            when_status: Tuple de status codes que disparan retry (ej: (429, 503))
            when_exception: Tuple de tipos de excepción que disparan retry
        
        Returns:
            self para permitir chaining con .get(), .post(), etc.
        
        Ejemplo:
            result = await http.retry(3, delay=2, when_status=(429, 503)).get("/api/data")
        """
        self._retry_attempts = attempts
        self._retry_delay = delay
        self._retry_backoff = backoff
        self._retry_when_status = when_status
        self._retry_when_exception = when_exception
        return self
    
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
        **kwargs: Any
    ) -> Result:
        """Método interno para realizar requests con retry y handlers.
        
        Args:
            method: Método HTTP (GET, POST, etc)
            url: URL del endpoint
            timeout: Timeout personalizado (sobrescribe config)
            follow_redirects: Si debe seguir redirecciones (sobrescribe config)
            on_before: Handler local para esta request (se ejecuta antes)
            on_after: Handler local para esta request (se ejecuta después)
            on_status: Dict de handlers por status code {404: handler, 200: handler}
            on_exception: Handler para excepciones
            **kwargs: Parámetros adicionales para httpx.request
        
        Returns:
            Result con response o exception
        """
        if not self._config.http_enable:
            raise HttpDisabledException

        import asyncio
        
        retry_attempts = self._retry_attempts if self._retry_attempts is not None else 0
        current_delay = self._retry_delay
        
        for attempt in range(retry_attempts + 1):
            try:
                client = await self._ensure_client()
                
                request_kwargs = kwargs.copy()
                if timeout is not None:
                    request_kwargs['timeout'] = timeout
                
                send_kwargs = {}
                if follow_redirects is not None:
                    send_kwargs['follow_redirects'] = follow_redirects
                
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
                
                if self._retry_when_status and result.status in self._retry_when_status:
                    if attempt < retry_attempts:
                        await asyncio.sleep(current_delay)
                        current_delay *= self._retry_backoff
                        continue
                
                self._clear_retry_config()
                return result
                
            except Exception as e:
                response = getattr(e, 'response', None)
                result = Result.from_exception(e, response)
                
                if on_exception:
                    on_exception(e)
                
                should_retry = False
                if self._retry_when_exception:
                    should_retry = isinstance(e, self._retry_when_exception)
                elif self._retry_attempts is not None:
                    should_retry = True
                
                if should_retry and attempt < retry_attempts:
                    await asyncio.sleep(current_delay)
                    current_delay *= self._retry_backoff
                    continue
                
                self._clear_retry_config()
                return result
        
        self._clear_retry_config()
        return result
    
    def _clear_retry_config(self) -> None:
        """Limpia configuración de retry después de la request."""
        self._retry_attempts = None
        self._retry_delay = 1.0
        self._retry_backoff = 2.0
        self._retry_when_status = None
        self._retry_when_exception = None
    
    async def get(
        self,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: Optional[float] = None,
        follow_redirects: Optional[bool] = None,
        on_before: Optional[Callable[[httpx.Request], None]] = None,
        on_after: Optional[Callable[[httpx.Request, httpx.Response], None]] = None,
        on_status: Optional[dict[int, Callable[[], None]]] = None,
        on_exception: Optional[Callable[[Exception], None]] = None,
        **kwargs: Any
    ) -> Result:
        """GET request con handlers opcionales.
        
        Args:
            url: URL del endpoint (requerido)
            params: Query parameters
            headers: Headers HTTP personalizados
            timeout: Timeout en segundos (sobrescribe config global)
            follow_redirects: Si debe seguir redirecciones 3xx
            on_before: Handler que se ejecuta antes de esta request
            on_after: Handler que se ejecuta después de esta request
            on_status: Dict de handlers por status {404: handler, 200: handler}
            on_exception: Handler para excepciones de esta request
            **kwargs: Argumentos adicionales para httpx.request
        
        Returns:
            Result con response o exception
        
        Ejemplos:
            # Simple
            result = await http.get("/users/1")
            
            # Con retry
            result = await http.retry(3, on_status=(429, 503)).get("/api/data")
            
            # Con handlers
            result = await http.get(
                "/users/1",
                on_status={404: lambda: print("Not found")},
                on_exception=lambda e: log_error(e)
            )
        """
        return await self._request(
            "GET", 
            url, 
            params=params, 
            headers=headers, 
            timeout=timeout,
            follow_redirects=follow_redirects,
            on_before=on_before,
            on_after=on_after,
            on_status=on_status,
            on_exception=on_exception,
            **kwargs
        )
    
    async def post(
        self,
        url: str,
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
        **kwargs: Any
    ) -> Result:
        """POST request con handlers opcionales.
        
        Args:
            url: URL del endpoint (requerido)
            json: Dict para enviar como JSON (Content-Type: application/json)
            data: Datos para form-urlencoded (Content-Type: application/x-www-form-urlencoded)
            content: Bytes puros (archivos, imágenes)
            headers: Headers HTTP personalizados
            timeout: Timeout en segundos
            follow_redirects: Si debe seguir redirecciones 3xx
            on_before: Handler que se ejecuta antes de esta request
            on_after: Handler que se ejecuta después de esta request
            on_status: Dict de handlers por status {201: handler, 400: handler}
            on_exception: Handler para excepciones de esta request
            **kwargs: Argumentos adicionales para httpx.request
        
        Returns:
            Result con response o exception
        
        Ejemplos:
            # JSON
            result = await http.post("/users", json={"name": "John"})
            
            # Con handlers
            result = await http.post(
                "/users",
                json={"name": "John"},
                on_status={201: lambda: print("Created!")}
            )
        """
        return await self._request(
            "POST", 
            url, 
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
            **kwargs
        )
    
    async def put(
        self,
        url: str,
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
        **kwargs: Any
    ) -> Result:
        """PUT request con handlers opcionales.
        
        Args:
            url: URL del endpoint (requerido)
            json: Dict para enviar como JSON
            data: Datos para form-urlencoded
            content: Bytes puros
            headers: Headers HTTP personalizados
            timeout: Timeout en segundos
            follow_redirects: Si debe seguir redirecciones 3xx
            on_before: Handler que se ejecuta antes de esta request
            on_after: Handler que se ejecuta después de esta request
            on_status: Dict de handlers por status
            on_exception: Handler para excepciones de esta request
            **kwargs: Argumentos adicionales para httpx.request
        
        Returns:
            Result con response o exception
        """
        return await self._request(
            "PUT", 
            url, 
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
            **kwargs
        )
    
    async def delete(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        timeout: Optional[float] = None,
        follow_redirects: Optional[bool] = None,
        on_before: Optional[Callable[[httpx.Request], None]] = None,
        on_after: Optional[Callable[[httpx.Request, httpx.Response], None]] = None,
        on_status: Optional[dict[int, Callable[[], None]]] = None,
        on_exception: Optional[Callable[[Exception], None]] = None,
        **kwargs: Any
    ) -> Result:
        """DELETE request con handlers opcionales.
        
        Args:
            url: URL del endpoint (requerido)
            headers: Headers HTTP personalizados
            timeout: Timeout en segundos
            follow_redirects: Si debe seguir redirecciones 3xx
            on_before: Handler que se ejecuta antes de esta request
            on_after: Handler que se ejecuta después de esta request
            on_status: Dict de handlers por status
            on_exception: Handler para excepciones de esta request
            **kwargs: Argumentos adicionales para httpx.request
        
        Returns:
            Result con response o exception
        """
        return await self._request(
            "DELETE", 
            url, 
            headers=headers,
            timeout=timeout,
            follow_redirects=follow_redirects,
            on_before=on_before,
            on_after=on_after,
            on_status=on_status,
            on_exception=on_exception,
            **kwargs
        )
    
    async def patch(
        self,
        url: str,
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
        **kwargs: Any
    ) -> Result:
        """PATCH request con handlers opcionales.
        
        Args:
            url: URL del endpoint (requerido)
            json: Dict para enviar como JSON
            data: Datos para form-urlencoded
            content: Bytes puros
            headers: Headers HTTP personalizados
            timeout: Timeout en segundos
            follow_redirects: Si debe seguir redirecciones 3xx
            on_before: Handler que se ejecuta antes de esta request
            on_after: Handler que se ejecuta después de esta request
            on_status: Dict de handlers por status
            on_exception: Handler para excepciones de esta request
            **kwargs: Argumentos adicionales para httpx.request
        
        Returns:
            Result con response o exception
        """
        return await self._request(
            "PATCH", 
            url, 
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
            **kwargs
        )
    
    async def close(self):
        """Cierra el cliente y libera recursos.
        
        Debe llamarse al finalizar la aplicación para liberar
        conexiones del pool correctamente.
        """
        if self._client:
            await self._client.aclose()
            self._client = None
