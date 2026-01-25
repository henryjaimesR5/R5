# HTTP Client - Características Avanzadas

Funcionalidades avanzadas del cliente HTTP para casos de uso complejos.

## Retry Automático

### Retry Básico

```python
@inject
async def fetch_with_retry(http: Http):
    result = await http.retry(
        attempts=3,
        delay=1.0,
        backoff=2.0
    ).get("https://api.example.com/data")
    
    return result
```

**Comportamiento:**
- Intento 1: inmediato
- Intento 2: espera 1.0s
- Intento 3: espera 2.0s (1.0 * 2.0)
- Intento 4: espera 4.0s (2.0 * 2.0)

### Retry en Status Codes Específicos

```python
@inject
async def retry_on_status(http: Http):
    result = await http.retry(
        attempts=5,
        delay=0.5,
        when_status=(429, 500, 502, 503, 504)
    ).get("https://api.example.com/data")
    
    # Solo reintenta si el status está en la tupla
    return result
```

**Casos de uso:**
- `429` - Rate limiting
- `500` - Internal server error
- `502` - Bad gateway
- `503` - Service unavailable
- `504` - Gateway timeout

### Retry en Excepciones

```python
import httpx

@inject
async def retry_on_exception(http: Http):
    result = await http.retry(
        attempts=3,
        delay=1.0,
        when_exception=(
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.ConnectError
        )
    ).get("https://api.example.com/data")
    
    return result
```

### Retry con Backoff Exponencial

```python
@inject
async def exponential_backoff(http: Http):
    result = await http.retry(
        attempts=5,
        delay=1.0,
        backoff=2.0  # Duplica el delay en cada intento
    ).get("https://api.example.com/data")
    
    # Delays: 1.0s, 2.0s, 4.0s, 8.0s, 16.0s
    return result
```

### Retry Combinado

```python
@inject
async def combined_retry(http: Http):
    result = await http.retry(
        attempts=5,
        delay=0.5,
        backoff=1.5,
        when_status=(429, 503),
        when_exception=(httpx.TimeoutException,)
    ).get("https://api.example.com/data")
    
    # Reintenta en status 429/503 O TimeoutException
    return result
```

## Handlers Globales

### Before Handler Global

Se ejecuta antes de TODAS las requests:

```python
@inject
async def setup_logging(http: Http):
    def log_request(request):
        print(f"→ {request.method} {request.url}")
        print(f"  Headers: {dict(request.headers)}")
    
    http.on_before(log_request)
    
    # Todas las requests logean automáticamente
    await http.get("https://api.example.com/users/1")
    await http.post("https://api.example.com/users", json={})
```

### After Handler Global

Se ejecuta después de TODAS las requests exitosas:

```python
@inject
async def setup_response_logging(http: Http):
    def log_response(request, response):
        print(f"← {response.status_code}")
        print(f"  Time: {response.elapsed.total_seconds()}s")
    
    http.on_after(log_response)
    
    await http.get("https://api.example.com/users/1")
```

### Múltiples Handlers

```python
@inject
async def multiple_handlers(http: Http):
    # Handler 1: Logging
    http.on_before(lambda req: print(f"→ {req.url}"))
    
    # Handler 2: Métricas
    http.on_before(lambda req: metrics.record_request(req))
    
    # Handler 3: Autenticación
    def add_auth(request):
        request.headers["Authorization"] = f"Bearer {get_token()}"
    
    http.on_before(add_auth)
    
    # Todos los handlers se ejecutan en orden
    await http.get("https://api.example.com/data")
```

### Handlers con Estado

```python
@inject
async def stateful_handlers(http: Http):
    request_count = {"count": 0}
    
    def count_requests(request):
        request_count["count"] += 1
        print(f"Request #{request_count['count']}")
    
    http.on_before(count_requests)
    
    await http.get("https://api.example.com/1")  # Request #1
    await http.get("https://api.example.com/2")  # Request #2
    await http.get("https://api.example.com/3")  # Request #3
```

## Configuración Avanzada

### HttpConfig Personalizada

```python
from R5.ioc import config
from R5.http.http import HttpConfig

@config(file='.env')
class ProductionHttpConfig(HttpConfig):
    # Connection Pool
    max_connections: int = 200
    max_keepalive_connections: int = 50
    keepalive_expiry: float = 10.0
    
    # Timeouts
    connect_timeout: float = 10.0
    read_timeout: float = 60.0
    write_timeout: float = 60.0
    pool_timeout: float = 10.0
    
    # Retry
    max_retries: int = 5
    retry_backoff_factor: float = 1.5
    retry_statuses: list[int] = [429, 500, 502, 503, 504]
    
    # Headers
    default_headers: dict[str, str] = {
        "User-Agent": "MyApp/1.0",
        "Accept": "application/json"
    }
    
    # Redirects
    follow_redirects: bool = True
```

### Proxy Configuration

```python
@config(file='.env')
class ProxyHttpConfig(HttpConfig):
    proxies: list[str] = [
        "http://proxy1:8080",
        "http://proxy2:8080",
        "http://proxy3:8080"
    ]
    proxy_rotation: bool = True
```

El cliente rotará automáticamente entre los proxies en cada request.

### Custom User-Agent

```python
@config
class CustomHttpConfig(HttpConfig):
    user_agent: str = "MyBot/2.0 (+https://mybot.com)"
```

## Proxy Rotation

### Configuración

```python
@config(file='.env')
class ProxyConfig(HttpConfig):
    proxies: list[str] = [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080",
        "http://proxy3.example.com:8080"
    ]
    proxy_rotation: bool = True
```

**Archivo .env:**
```env
PROXIES=http://proxy1:8080,http://proxy2:8080,http://proxy3:8080
PROXY_ROTATION=true
```

### Uso

```python
@inject
async def with_proxy_rotation(http: Http):
    # Request 1 usa proxy1
    result1 = await http.get("https://api.example.com/data")
    
    # Request 2 usa proxy2
    result2 = await http.get("https://api.example.com/data")
    
    # Request 3 usa proxy3
    result3 = await http.get("https://api.example.com/data")
    
    # Request 4 vuelve a proxy1 (round-robin)
    result4 = await http.get("https://api.example.com/data")
```

## Métricas y Monitoring

### Tracking de Requests

```python
from dataclasses import dataclass
from typing import Dict
import time

@dataclass
class RequestMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_time: float = 0.0
    
    def avg_time(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_time / self.total_requests

@inject
async def track_metrics(http: Http):
    metrics = RequestMetrics()
    
    def before_handler(request):
        request._start_time = time.time()
    
    def after_handler(request, response):
        elapsed = time.time() - request._start_time
        metrics.total_requests += 1
        metrics.total_time += elapsed
        
        if 200 <= response.status_code < 300:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        print(f"Request took {elapsed:.3f}s")
    
    http.on_before(before_handler)
    http.on_after(after_handler)
    
    # Hacer requests
    for i in range(10):
        await http.get(f"https://api.example.com/items/{i}")
    
    print(f"Total: {metrics.total_requests}")
    print(f"Success: {metrics.successful_requests}")
    print(f"Failed: {metrics.failed_requests}")
    print(f"Avg Time: {metrics.avg_time():.3f}s")
```

### Logging Detallado

```python
import logging

logger = logging.getLogger(__name__)

@inject
async def detailed_logging(http: Http):
    def log_before(request):
        logger.info(f"→ {request.method} {request.url}")
        logger.debug(f"  Headers: {dict(request.headers)}")
    
    def log_after(request, response):
        logger.info(f"← {response.status_code}")
        logger.debug(f"  Response headers: {dict(response.headers)}")
        logger.debug(f"  Content length: {len(response.content)}")
    
    http.on_before(log_before)
    http.on_after(log_after)
    
    await http.get("https://api.example.com/data")
```

## Rate Limiting

### Manual Rate Limiting

```python
import asyncio
from asyncio import Semaphore

@inject
async def rate_limited_requests(http: Http):
    # Máximo 5 requests concurrentes
    semaphore = Semaphore(5)
    
    async def limited_get(url: str):
        async with semaphore:
            result = await http.get(url)
            await asyncio.sleep(0.2)  # 200ms entre requests
            return result
    
    tasks = [
        limited_get(f"https://api.example.com/items/{i}")
        for i in range(100)
    ]
    
    results = await asyncio.gather(*tasks)
    return results
```

### Token Bucket Rate Limiter

```python
import time
from asyncio import Lock

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = Lock()
    
    async def acquire(self):
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1

@inject
async def with_token_bucket(http: Http):
    # 10 requests por segundo, burst de 20
    limiter = TokenBucket(rate=10, capacity=20)
    
    for i in range(100):
        await limiter.acquire()
        result = await http.get(f"https://api.example.com/items/{i}")
```

## Circuit Breaker

### Implementación Básica

```python
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
    
    def record_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED
    
    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def can_attempt(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        
        return True  # HALF_OPEN

@inject
async def with_circuit_breaker(http: Http):
    breaker = CircuitBreaker(failure_threshold=3, timeout=30.0)
    
    async def protected_request(url: str):
        if not breaker.can_attempt():
            print("Circuit breaker OPEN, skipping request")
            return None
        
        result = await http.get(url)
        
        if result.status == 200:
            breaker.record_success()
        else:
            breaker.record_failure()
        
        return result
    
    for i in range(10):
        result = await protected_request("https://api.example.com/data")
        await asyncio.sleep(1)
```

## Autenticación Avanzada

### OAuth 2.0

```python
@singleton
class OAuth2Manager:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.expires_at = 0
    
    async def get_access_token(self, http: Http) -> str:
        if time.time() < self.expires_at:
            return self.access_token
        
        # Refresh token
        result = await http.post(
            "https://auth.example.com/oauth/token",
            json={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": "your-client-id"
            }
        )
        
        data = result.to(dict)
        self.access_token = data["access_token"]
        self.expires_at = time.time() + data["expires_in"]
        
        return self.access_token

@inject
async def authenticated_requests(http: Http, oauth: OAuth2Manager):
    token = await oauth.get_access_token(http)
    
    result = await http.get(
        "https://api.example.com/protected",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    return result
```

### JWT Auto-Refresh

```python
import jwt
from datetime import datetime

@singleton
class JWTManager:
    def __init__(self):
        self.token = None
    
    def is_expired(self) -> bool:
        if not self.token:
            return True
        
        try:
            payload = jwt.decode(self.token, options={"verify_signature": False})
            exp = datetime.fromtimestamp(payload['exp'])
            return datetime.now() >= exp
        except:
            return True
    
    async def refresh_if_needed(self, http: Http):
        if self.is_expired():
            result = await http.post(
                "https://auth.example.com/refresh",
                json={"refresh_token": self.refresh_token}
            )
            self.token = result.to(dict)["access_token"]
```

## Caching

### Response Cache

```python
from typing import Optional
import hashlib
import json

@singleton
class ResponseCache:
    def __init__(self):
        self._cache: Dict[str, tuple[float, Any]] = {}
        self.ttl = 300  # 5 minutos
    
    def _make_key(self, url: str, params: dict) -> str:
        data = f"{url}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, url: str, params: dict) -> Optional[Any]:
        key = self._make_key(url, params)
        if key in self._cache:
            timestamp, value = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return value
        return None
    
    def set(self, url: str, params: dict, value: Any):
        key = self._make_key(url, params)
        self._cache[key] = (time.time(), value)

@inject
async def cached_requests(http: Http, cache: ResponseCache):
    url = "https://api.example.com/data"
    params = {"page": 1}
    
    # Check cache
    cached = cache.get(url, params)
    if cached:
        print("Cache hit!")
        return cached
    
    # Fetch from API
    result = await http.get(url, params=params)
    data = result.to(dict)
    
    # Store in cache
    cache.set(url, params, data)
    
    return data
```

## WebSocket Support

Para WebSockets, usa httpx directamente o una librería dedicada:

```python
@inject
async def websocket_example(http: Http):
    # http no soporta WebSockets directamente
    # Usa websockets library
    import websockets
    
    async with websockets.connect("wss://example.com/ws") as ws:
        await ws.send("Hello")
        response = await ws.recv()
        return response
```

## Próximos Pasos

- [Result Pattern](result.md) - Manejo avanzado de Result
- [Basic Usage](basic-usage.md) - Uso básico del cliente
- [API Reference](../../api/http.md) - Documentación completa
