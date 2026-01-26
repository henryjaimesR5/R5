import pytest
import warnings
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import dataclass
from typing import Optional
import httpx

from R5.http import Http, Result
from R5.http.http import HttpConfig
from R5.ioc import Container, inject


@dataclass
class TestUser:
    id: int
    name: str
    email: str


@dataclass
class TestUserWithOptional:
    id: int
    name: str
    email: Optional[str]


@dataclass
class StrictUser:
    id: int
    name: str
    email: str


@dataclass
class AllOptionalUser:
    id: Optional[int]
    name: Optional[str]
    email: Optional[str]


@pytest.fixture
def http_config():
    """Config básica para tests."""
    config = HttpConfig()
    config.max_connections = 10
    config.connect_timeout = 5.0
    config.proxies = ["http://proxy1:8080", "http://proxy2:8080"]
    return config


@pytest.fixture
def http_client(http_config):
    """Cliente HTTP para tests."""
    return Http(http_config)


@pytest.fixture
def mock_response():
    """Mock de httpx.Response."""
    response = Mock(spec=httpx.Response)
    response.status_code = 200
    response.json.return_value = {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com"
    }
    response.text = '{"id": 1, "name": "John Doe"}'
    
    request = Mock(spec=httpx.Request)
    request.url = "https://api.example.com/users/1"
    response.request = request
    
    return response


class TestResult:
    """Tests para la clase Result."""
    
    def test_from_response_success(self, mock_response):
        """Test creación de Result desde response exitosa."""
        result = Result.from_response(mock_response)
        
        assert result.response == mock_response
        assert result.status == 200
        assert result.exception is None
        assert result.request == mock_response.request
    
    def test_from_exception(self):
        """Test creación de Result desde excepción."""
        error = Exception("Network error")
        result = Result.from_exception(error)
        
        assert result.exception == error
        assert result.status == 0
        assert result.response is None
    
    def test_from_exception_with_response(self, mock_response):
        """Test Result desde excepción con response."""
        mock_response.status_code = 500
        error = Exception("Server error")
        
        result = Result.from_exception(error, mock_response)
        
        assert result.exception == error
        assert result.status == 500
        assert result.response == mock_response
    
    def test_on_status_matches(self, mock_response):
        """Test on_status cuando status coincide."""
        result = Result.from_response(mock_response)
        handler_called = []
        
        result.on_status(200, lambda req, res: handler_called.append(True))
        
        assert len(handler_called) == 1
    
    def test_on_status_no_match(self, mock_response):
        """Test on_status cuando status no coincide."""
        result = Result.from_response(mock_response)
        handler_called = []
        
        result.on_status(404, lambda req, res: handler_called.append(True))
        
        assert len(handler_called) == 0
    
    def test_on_exception_with_exception(self):
        """Test on_exception cuando hay excepción."""
        error = Exception("Test error")
        result = Result.from_exception(error)
        handler_called = []
        
        result.on_exception(lambda e: handler_called.append(str(e)))
        
        assert len(handler_called) == 1
        assert handler_called[0] == "Test error"
    
    def test_on_exception_no_exception(self, mock_response):
        """Test on_exception cuando no hay excepción."""
        result = Result.from_response(mock_response)
        handler_called = []
        
        result.on_exception(lambda e: handler_called.append(True))
        
        assert len(handler_called) == 0
    
    def test_chaining_handlers(self, mock_response):
        """Test chaining de múltiples handlers."""
        result = Result.from_response(mock_response)
        calls = []
        
        result.on_status(200, lambda req, res: calls.append("status_200"))
        result.on_status(404, lambda req, res: calls.append("status_404"))
        result.on_exception(lambda e: calls.append("exception"))
        
        assert calls == ["status_200"]
    
    def test_to_dict(self, mock_response):
        """Test mapeo a dict."""
        result = Result.from_response(mock_response)
        data = result.to(dict)
        
        assert data is not None
        assert data["id"] == 1
        assert data["name"] == "John Doe"
    
    def test_to_with_exception(self):
        """Test to() cuando hay excepción."""
        error = Exception("Network error")
        result = Result.from_exception(error)
        
        data = result.to(dict)
        
        assert data is None


class TestHttp:
    """Tests para la clase Http."""
    
    @pytest.mark.asyncio
    async def test_get_basic(self, http_client):
        """Test GET request básica."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request = Mock(spec=httpx.Request)
        mock_request.url = "https://api.example.com/test"
        mock_response.request = mock_request
        
        async with http_client:
            with patch.object(httpx.AsyncClient, 'send', new_callable=AsyncMock) as mock_send:
                mock_send.return_value = mock_response
                
                result = await http_client.get("https://api.example.com/test")
                
                assert result.status == 200
                assert result.response == mock_response
                mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_post_with_json(self, http_client):
        """Test POST con JSON."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1, "data": "created"}
        mock_request = Mock(spec=httpx.Request)
        mock_request.url = "https://api.example.com/test"
        mock_response.request = mock_request
        
        async with http_client:
            with patch.object(httpx.AsyncClient, 'send', new_callable=AsyncMock) as mock_send:
                mock_send.return_value = mock_response
                
                result = await http_client.post(
                    "https://api.example.com/test",
                    json={"data": "test"}
                )
                
                assert result.status == 201
                assert result.response == mock_response
                mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_put_request(self, http_client):
        """Test PUT request."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_request = Mock(spec=httpx.Request)
        mock_request.url = "https://api.example.com/test/1"
        mock_response.request = mock_request
        
        async with http_client:
            with patch.object(httpx.AsyncClient, 'send', new_callable=AsyncMock) as mock_send:
                mock_send.return_value = mock_response
                
                result = await http_client.put(
                    "https://api.example.com/test/1",
                    json={"data": "updated"}
                )
                
                assert result.status == 200
    
    @pytest.mark.asyncio
    async def test_delete_request(self, http_client):
        """Test DELETE request."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 204
        mock_request = Mock(spec=httpx.Request)
        mock_request.url = "https://api.example.com/test/1"
        mock_response.request = mock_request
        
        async with http_client:
            with patch.object(httpx.AsyncClient, 'send', new_callable=AsyncMock) as mock_send:
                mock_send.return_value = mock_response
                
                result = await http_client.delete("https://api.example.com/test/1")
                
                assert result.status == 204
    
    @pytest.mark.asyncio
    async def test_patch_request(self, http_client):
        """Test PATCH request."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_request = Mock(spec=httpx.Request)
        mock_request.url = "https://api.example.com/test/1"
        mock_response.request = mock_request
        
        async with http_client:
            with patch.object(httpx.AsyncClient, 'send', new_callable=AsyncMock) as mock_send:
                mock_send.return_value = mock_response
                
                result = await http_client.patch(
                    "https://api.example.com/test/1",
                    json={"data": "patched"}
                )
                
                assert result.status == 200
    
    @pytest.mark.asyncio
    async def test_request_with_exception(self, http_client):
        """Test request que lanza excepción."""
        async with http_client:
            with patch.object(httpx.AsyncClient, 'send', new_callable=AsyncMock) as mock_send:
                mock_send.side_effect = httpx.TimeoutException("Timeout")
                
                result = await http_client.get("https://api.example.com/test")
                
                assert result.exception is not None
                assert isinstance(result.exception, httpx.TimeoutException)
                assert result.status == 0
    
    @pytest.mark.asyncio
    async def test_custom_timeout(self, http_client):
        """Test request con timeout personalizado."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_request = Mock(spec=httpx.Request)
        mock_request.url = "https://api.example.com/test"
        mock_response.request = mock_request
        
        async with http_client:
            with patch.object(httpx.AsyncClient, 'send', new_callable=AsyncMock) as mock_send:
                mock_send.return_value = mock_response
                
                result = await http_client.get(
                    "https://api.example.com/test",
                    timeout=10.0
                )
                
                assert result.status == 200
    
    @pytest.mark.asyncio
    async def test_custom_headers(self, http_client):
        """Test request con headers personalizados."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_request = Mock(spec=httpx.Request)
        mock_request.url = "https://api.example.com/test"
        mock_response.request = mock_request
        
        async with http_client:
            with patch.object(httpx.AsyncClient, 'send', new_callable=AsyncMock) as mock_send:
                mock_send.return_value = mock_response
                
                custom_headers = {"Authorization": "Bearer token123"}
                result = await http_client.get(
                    "https://api.example.com/test",
                    headers=custom_headers
                )
                
                assert result.status == 200
    
    @pytest.mark.asyncio
    async def test_proxy_rotation(self, http_client):
        """Test rotación de proxies."""
        proxy1 = http_client._get_proxy()
        proxy2 = http_client._get_proxy()
        proxy3 = http_client._get_proxy()
        
        assert proxy1 == "http://proxy1:8080"
        assert proxy2 == "http://proxy2:8080"
        assert proxy3 == "http://proxy1:8080"
    
    @pytest.mark.asyncio
    async def test_close(self, http_client):
        """Test cierre del cliente."""
        mock_client = AsyncMock()
        http_client._client = mock_client
        
        await http_client.close()
        
        mock_client.aclose.assert_called_once()
        assert http_client._client is None


class TestHttpConfig:
    """Tests para HttpConfig."""
    
    def test_default_config(self):
        """Test configuración por defecto."""
        config = HttpConfig()
        
        assert config.max_connections == 100
        assert config.connect_timeout == 5.0
        assert config.user_agent == "R5-HttpClient/1.0"
        assert config.follow_redirects is True
    
    def test_custom_config(self):
        """Test configuración personalizada."""
        config = HttpConfig()
        config.max_connections = 50
        config.connect_timeout = 10.0
        config.proxies = ["http://proxy:8080"]
        
        assert config.max_connections == 50
        assert config.connect_timeout == 10.0
        assert config.proxies == ["http://proxy:8080"]
    
    def test_config_validation(self):
        """Test validación de configuración."""
        config = HttpConfig()
        config.max_connections = 200
        assert config.max_connections == 200


class TestIntegrationWithIoC:
    """Tests de integración con IoC container."""
    
    @pytest.mark.asyncio
    async def test_resolve_http_from_container(self):
        """Test resolver Http desde container como resource."""
        container = Container()
        
        http_resource = container.resolve(Http)
        async with await http_resource as http:
            assert http is not None
            assert isinstance(http, Http)
    
    @pytest.mark.asyncio
    async def test_http_with_inject_decorator(self):
        """Test Http funciona correctamente con @inject sin necesidad de close() manual."""
        @inject
        async def fetch_data(http: Http):
            result = await http.get("https://httpbin.org/get")
            return result.to(dict)
        
        async with await Container.resolve(Http) as http:
            data = await fetch_data(http)
            assert data is not None


class TestInterceptors:
    """Tests para interceptors on_before y on_after."""
    
    @pytest.mark.asyncio
    async def test_on_before_is_called(self):
        """Test on_before se ejecuta antes de cada request."""
        config = HttpConfig()
        http = Http(config)
        
        called = []
        
        def before_handler(request: httpx.Request):
            called.append(f"before:{request.method}:{request.url}")
        
        http.on_before(before_handler)
        
        async with http:
            result = await http.get("https://httpbin.org/get")
            assert result.status == 200
        
        assert len(called) == 1
        assert "before:GET:" in called[0]
        assert "httpbin.org/get" in called[0]
    
    @pytest.mark.asyncio
    async def test_on_after_is_called(self):
        """Test on_after se ejecuta después de cada request exitosa."""
        config = HttpConfig()
        http = Http(config)
        
        called = []
        
        def after_handler(request: httpx.Request, response: httpx.Response):
            called.append(f"after:{request.method}:{response.status_code}")
        
        http.on_after(after_handler)
        
        async with http:
            result = await http.get("https://httpbin.org/get")
            assert result.status == 200
        
        assert len(called) == 1
        assert called[0] == "after:GET:200"
    
    @pytest.mark.asyncio
    async def test_multiple_before_handlers(self):
        """Test múltiples on_before handlers se ejecutan en orden."""
        config = HttpConfig()
        http = Http(config)
        
        called = []
        
        http.on_before(lambda req: called.append("handler1"))
        http.on_before(lambda req: called.append("handler2"))
        http.on_before(lambda req: called.append("handler3"))
        
        async with http:
            await http.get("https://httpbin.org/get")
        
        assert called == ["handler1", "handler2", "handler3"]
    
    @pytest.mark.asyncio
    async def test_multiple_after_handlers(self):
        """Test múltiples on_after handlers se ejecutan en orden."""
        config = HttpConfig()
        http = Http(config)
        
        called = []
        
        http.on_after(lambda req, res: called.append("handler1"))
        http.on_after(lambda req, res: called.append("handler2"))
        http.on_after(lambda req, res: called.append("handler3"))
        
        async with http:
            await http.get("https://httpbin.org/get")
        
        assert called == ["handler1", "handler2", "handler3"]
    
    @pytest.mark.asyncio
    async def test_interceptors_chaining(self):
        """Test interceptors soportan chaining."""
        config = HttpConfig()
        http = Http(config)
        
        result = (http
            .on_before(lambda req: None)
            .on_after(lambda req, res: None)
            .on_before(lambda req: None))
        
        assert result is http
        assert len(http._before_handlers) == 2
        assert len(http._after_handlers) == 1
    
    @pytest.mark.asyncio
    async def test_interceptors_with_multiple_requests(self):
        """Test interceptors se ejecutan en cada request."""
        config = HttpConfig()
        http = Http(config)
        
        request_count = []
        
        http.on_before(lambda req: request_count.append(1))
        
        async with http:
            await http.get("https://httpbin.org/get")
            await http.post("https://httpbin.org/post", json={"test": "data"})
            await http.get("https://httpbin.org/uuid")
        
        assert len(request_count) == 3
    
    @pytest.mark.asyncio
    async def test_before_handler_can_inspect_request(self):
        """Test on_before puede inspeccionar y modificar request."""
        config = HttpConfig()
        http = Http(config)
        
        inspected = {}
        
        def inspect_handler(request: httpx.Request):
            inspected['method'] = request.method
            inspected['url'] = str(request.url)
            inspected['headers'] = dict(request.headers)
        
        http.on_before(inspect_handler)
        
        async with http:
            await http.get("https://httpbin.org/get", headers={"X-Custom": "test"})
        
        assert inspected['method'] == 'GET'
        assert 'httpbin.org/get' in inspected['url']
        assert 'x-custom' in inspected['headers']
        assert inspected['headers']['x-custom'] == 'test'
    
    @pytest.mark.asyncio
    async def test_after_handler_can_inspect_response(self):
        """Test on_after puede inspeccionar response."""
        config = HttpConfig()
        http = Http(config)
        
        inspected = {}
        
        def inspect_handler(request: httpx.Request, response: httpx.Response):
            inspected['status'] = response.status_code
            inspected['headers'] = dict(response.headers)
            inspected['request_url'] = str(request.url)
        
        http.on_after(inspect_handler)
        
        async with http:
            await http.get("https://httpbin.org/get")
        
        assert inspected['status'] == 200
        assert 'content-type' in inspected['headers']
        assert 'httpbin.org/get' in inspected['request_url']


class TestRetryWithWhenConditions:
    """Tests para Http.retry() con when_status y when_exception."""
    
    @pytest.mark.asyncio
    async def test_retry_with_when_status(self):
        """Test retry con when_status - reintenta en status específicos."""
        config = HttpConfig()
        http = Http(config)
        
        call_count = []
        
        async with http:
            # Simula que la primera llamada falla con 503, segunda con 200
            with patch.object(http, '_ensure_client') as mock_client_getter:
                mock_client = AsyncMock()
                mock_client_getter.return_value = mock_client
                
                # Primera llamada: 503
                # Segunda llamada: 200
                responses = []
                
                response_503 = Mock(spec=httpx.Response)
                response_503.status_code = 503
                request_503 = Mock(spec=httpx.Request)
                request_503.url = "http://test.com"
                request_503.method = "GET"
                response_503.request = request_503
                
                response_200 = Mock(spec=httpx.Response)
                response_200.status_code = 200
                request_200 = Mock(spec=httpx.Request)
                request_200.url = "http://test.com"
                request_200.method = "GET"
                response_200.request = request_200
                
                async def mock_send(req):
                    call_count.append(1)
                    if len(call_count) == 1:
                        return response_503
                    return response_200
                
                mock_client.build_request = Mock(side_effect=lambda *args, **kwargs: request_200)
                mock_client.send = AsyncMock(side_effect=mock_send)
                
                # Test: retry cuando recibe 503
                result = await http.retry(
                    attempts=3,
                    delay=0.01,
                    when_status=(503,)  # Condición PARA reintentar
                ).get("http://test.com")
                
                assert result.status == 200
                assert len(call_count) == 2  # Primera falló (503), segunda exitosa (200)
    
    @pytest.mark.asyncio
    async def test_on_status_vs_when_status(self):
        """Test diferencia entre on_status (handler) y when_status (retry condition)."""
        config = HttpConfig()
        http = Http(config)
        
        on_status_called = []
        retry_count = []
        
        async with http:
            # Test 1: on_status ejecuta handler, NO reintenta
            result = await http.get(
                "https://httpbin.org/status/404",
                on_status={
                    404: lambda: on_status_called.append("handler_404")
                }
            )
            
            assert result.status == 404
            assert "handler_404" in on_status_called
            
            # Test 2: when_status reintenta (simulado con mock)
            on_status_called.clear()
            
            with patch.object(http, '_ensure_client') as mock_client_getter:
                mock_client = AsyncMock()
                mock_client_getter.return_value = mock_client
                
                response_404 = Mock(spec=httpx.Response)
                response_404.status_code = 404
                request = Mock(spec=httpx.Request)
                request.url = "http://test.com"
                request.method = "GET"
                response_404.request = request
                
                async def mock_send(req):
                    retry_count.append(1)
                    return response_404
                
                mock_client.build_request = Mock(return_value=request)
                mock_client.send = AsyncMock(side_effect=mock_send)
                
                result = await http.retry(
                    attempts=2,
                    delay=0.01,
                    when_status=(404,)  # CONDICIÓN para reintentar
                ).get(
                    "http://test.com",
                    on_status={404: lambda: on_status_called.append("handler_404")}  # HANDLER a ejecutar
                )
                
                assert result.status == 404
                assert len(retry_count) == 3  # Intento inicial + 2 retries
                assert len(on_status_called) == 3  # Handler se ejecuta en cada intento
    
    @pytest.mark.asyncio
    async def test_retry_without_when_conditions_does_not_retry(self):
        """Test que sin when_status/when_exception, no reintenta automáticamente."""
        config = HttpConfig()
        http = Http(config)
        
        call_count = []
        
        async with http:
            with patch.object(http, '_ensure_client') as mock_client_getter:
                mock_client = AsyncMock()
                mock_client_getter.return_value = mock_client
                
                response = Mock(spec=httpx.Response)
                response.status_code = 503
                request = Mock(spec=httpx.Request)
                request.url = "http://test.com"
                request.method = "GET"
                response.request = request
                
                async def mock_send(req):
                    call_count.append(1)
                    return response
                
                mock_client.build_request = Mock(return_value=request)
                mock_client.send = AsyncMock(side_effect=mock_send)
                
                # retry() sin when_status no reintenta en 503
                result = await http.retry(
                    attempts=3,
                    delay=0.01
                    # Sin when_status ni when_exception
                ).get("http://test.com")
                
                assert result.status == 503
                assert len(call_count) == 1  # Solo 1 intento, no reintenta
    
    @pytest.mark.asyncio
    async def test_on_exception_handler_vs_when_exception_retry(self):
        """Test diferencia entre on_exception (handler) y when_exception (retry)."""
        config = HttpConfig()
        http = Http(config)
        
        on_exception_called = []
        
        async with http:
            # Test 1: on_exception ejecuta handler cuando hay error
            with patch.object(http, '_ensure_client') as mock_client_getter:
                mock_client = AsyncMock()
                mock_client_getter.return_value = mock_client
                
                request = Mock(spec=httpx.Request)
                request.url = "http://test.com"
                request.method = "GET"
                
                mock_client.build_request = Mock(return_value=request)
                mock_client.send = AsyncMock(side_effect=httpx.ConnectTimeout("Timeout"))
                
                result = await http.get(
                    "http://test.com",
                    on_exception=lambda e: on_exception_called.append(type(e).__name__)
                )
                
                assert result.exception is not None
                assert "ConnectTimeout" in on_exception_called
    
    @pytest.mark.asyncio
    async def test_combined_when_and_on_handlers(self):
        """Test combinación de when_* (retry conditions) con on_* (handlers)."""
        config = HttpConfig()
        http = Http(config)
        
        events = []
        
        async with http:
            with patch.object(http, '_ensure_client') as mock_client_getter:
                mock_client = AsyncMock()
                mock_client_getter.return_value = mock_client
                
                call_count = [0]
                
                async def mock_send(req):
                    call_count[0] += 1
                    response = Mock(spec=httpx.Response)
                    # Primera llamada: 503, segunda: 200
                    response.status_code = 503 if call_count[0] == 1 else 200
                    request_mock = Mock(spec=httpx.Request)
                    request_mock.url = "http://test.com"
                    request_mock.method = "GET"
                    response.request = request_mock
                    return response
                
                request = Mock(spec=httpx.Request)
                request.url = "http://test.com"
                request.method = "GET"
                
                mock_client.build_request = Mock(return_value=request)
                mock_client.send = AsyncMock(side_effect=mock_send)
                
                result = await http.retry(
                    attempts=2,
                    delay=0.01,
                    when_status=(503,)  # CUÁNDO reintentar
                ).get(
                    "http://test.com",
                    on_before=lambda req: events.append("before"),
                    on_after=lambda req, res: events.append(f"after:{res.status_code}"),
                    on_status={
                        200: lambda: events.append("status:200"),  # QUÉ hacer
                        503: lambda: events.append("status:503")
                    }
                )
                
                assert result.status == 200
                assert call_count[0] == 2  # Retry funcionó
                assert events.count("before") == 2  # on_before se ejecuta en cada intento
                assert events.count("after:503") == 1  # Primera respuesta
                assert events.count("after:200") == 1  # Segunda respuesta
                assert events.count("status:503") == 1  # Handler para 503
                assert events.count("status:200") == 1  # Handler para 200


class TestResultNullValidation:
    """Tests para validación de valores None en campos no-opcionales."""
    
    def test_optional_field_with_none_no_warning(self):
        """Campo opcional con None no debe emitir warning."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {
            "id": 1,
            "name": "John",
            "email": None
        }
        
        result = Result(response=mock_response, status=200)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            user = result.to(TestUserWithOptional)
            
            assert len(w) == 0
            assert user is not None
            assert user.id == 1
            assert user.name == "John"
            assert user.email is None
    
    def test_non_optional_field_with_none_emits_warning(self):
        """Campo no-opcional con None debe emitir warning."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {
            "id": 1,
            "name": None,
            "email": "test@example.com"
        }
        
        result = Result(response=mock_response, status=200)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            user = result.to(StrictUser)
            
            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "name" in str(w[0].message)
            assert "not typed as Optional" in str(w[0].message)
            assert "StrictUser" in str(w[0].message)
            
            assert user is not None
            assert user.id == 1
            assert user.name is None
            assert user.email == "test@example.com"
    
    def test_multiple_non_optional_fields_with_none_emits_warning(self):
        """Múltiples campos no-opcionales con None deben emitir warning."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {
            "id": None,
            "name": None,
            "email": None
        }
        
        result = Result(response=mock_response, status=200)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            user = result.to(StrictUser)
            
            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            
            message = str(w[0].message)
            assert "id" in message
            assert "name" in message
            assert "email" in message
            
            assert user is not None
    
    def test_all_optional_fields_with_none_no_warning(self):
        """Todos los campos opcionales con None no deben emitir warning."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {
            "id": None,
            "name": None,
            "email": None
        }
        
        result = Result(response=mock_response, status=200)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            user = result.to(AllOptionalUser)
            
            assert len(w) == 0
            assert user is not None
            assert user.id is None
            assert user.name is None
            assert user.email is None
    
    def test_non_optional_field_with_value_no_warning(self):
        """Campo no-opcional con valor no debe emitir warning."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {
            "id": 1,
            "name": "John",
            "email": "test@example.com"
        }
        
        result = Result(response=mock_response, status=200)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            user = result.to(StrictUser)
            
            assert len(w) == 0
            assert user is not None
            assert user.id == 1
            assert user.name == "John"
            assert user.email == "test@example.com"
    
    def test_missing_field_no_warning(self):
        """Campo faltante en JSON no debe emitir warning de None."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {
            "id": 1,
            "name": "John"
        }
        
        result = Result(response=mock_response, status=200)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                user = result.to(TestUserWithOptional)
            except TypeError:
                pass
            
            warning_messages = [str(warning.message) for warning in w if issubclass(warning.category, UserWarning)]
            assert not any("not typed as Optional" in msg for msg in warning_messages)
    
    def test_validation_only_for_dataclass(self):
        """Validación solo aplica a dataclass, no a dict."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {
            "id": None,
            "name": None,
            "email": None
        }
        
        result = Result(response=mock_response, status=200)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            data = result.to(dict)
            
            assert len(w) == 0
            assert data is not None
            assert data["id"] is None
            assert data["name"] is None
    
    def test_is_optional_type_detects_optional(self):
        """_is_optional_type debe detectar correctamente Optional[T]."""
        result = Result()
        
        assert result._is_optional_type(Optional[str]) is True
        assert result._is_optional_type(Optional[int]) is True
        assert result._is_optional_type(str) is False
        assert result._is_optional_type(int) is False
    
    def test_validate_null_values_returns_non_optional_fields(self):
        """_validate_null_values debe retornar campos con None que no son Optional."""
        result = Result()
        
        data = {"id": 1, "name": None, "email": None}
        null_fields = result._validate_null_values(data, TestUserWithOptional)
        
        assert "name" in null_fields
        assert "email" not in null_fields
        assert "id" not in null_fields
        assert len(null_fields) == 1
    
    def test_dataclass_mapping_with_mixed_null_values(self):
        """Test mapeo de dataclass con valores nulos mixtos."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {
            "id": 100,
            "name": "Alice",
            "email": None
        }
        
        result = Result(response=mock_response, status=200)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            user = result.to(TestUserWithOptional)
            
            assert len(w) == 0
            assert user.id == 100
            assert user.name == "Alice"
            assert user.email is None
