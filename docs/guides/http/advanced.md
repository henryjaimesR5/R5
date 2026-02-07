# HTTP Client - Características Avanzadas

## Retry Automático

```python
@inject
async def fetch_with_retry(http: Http):
    result = await http.retry(
        attempts=5,
        delay=0.5,
        backoff=2.0,
        when_status=(429, 500, 502, 503, 504),
        when_exception=(httpx.TimeoutException, httpx.NetworkError)
    ).get("https://api.example.com/data")

    return result
```

| Parámetro | Descripción | Default |
|---|---|---|
| `attempts` | Número máximo de intentos | 3 |
| `delay` | Delay inicial entre intentos (segundos) | 1.0 |
| `backoff` | Multiplicador exponencial del delay | 2.0 |
| `when_status` | Tupla de status codes que disparan retry | `()` |
| `when_exception` | Tupla de excepciones que disparan retry | `()` |

**Ejemplo de backoff**: delay=1.0, backoff=2.0 → esperas de 1s, 2s, 4s, 8s...

## Handlers Globales

Se ejecutan en **todas** las requests del cliente:

```python
@inject
async def setup_handlers(http: Http):
    # Before: se ejecuta antes de cada request
    http.on_before(lambda req: print(f"→ {req.method} {req.url}"))

    # After: se ejecuta después de cada request exitosa
    http.on_after(lambda req, res: print(f"← {res.status_code}"))

    # Múltiples handlers se ejecutan en orden de registro
    http.on_before(lambda req: metrics.record_request(req))
```

### Ejemplo: Métricas

```python
@dataclass
class RequestMetrics:
    total: int = 0
    successful: int = 0
    failed: int = 0

@inject
async def track_metrics(http: Http):
    metrics = RequestMetrics()

    def before(request):
        request._start_time = time.time()

    def after(request, response):
        metrics.total += 1
        if 200 <= response.status_code < 300:
            metrics.successful += 1
        else:
            metrics.failed += 1

    http.on_before(before)
    http.on_after(after)
```

## Configuración Avanzada

### HttpConfig

```python
from R5.ioc import config
from R5.http.http import HttpConfig

@config(file='.env')
class ProductionHttpConfig(HttpConfig):
    max_connections: int = 200
    max_keepalive_connections: int = 50
    keepalive_expiry: float = 10.0
    connect_timeout: float = 10.0
    read_timeout: float = 60.0
    write_timeout: float = 60.0
    pool_timeout: float = 10.0
    follow_redirects: bool = True
    default_headers: dict[str, str] = {
        "User-Agent": "MyApp/1.0",
        "Accept": "application/json"
    }
```

## Proxy Rotation

```python
@config(file='.env')
class ProxyConfig(HttpConfig):
    proxies: list[str] = [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080",
        "http://proxy3.example.com:8080"
    ]
    proxy_rotation: bool = True  # Round-robin automático
```

```env
# .env
PROXIES=http://proxy1:8080,http://proxy2:8080,http://proxy3:8080
PROXY_ROTATION=true
```

## Rate Limiting

```python
from asyncio import Semaphore

@inject
async def rate_limited(http: Http):
    semaphore = Semaphore(5)  # Máximo 5 concurrentes

    async def limited_get(url: str):
        async with semaphore:
            result = await http.get(url)
            await asyncio.sleep(0.2)
            return result

    tasks = [limited_get(f"https://api.example.com/items/{i}") for i in range(100)]
    return await asyncio.gather(*tasks)
```

## Circuit Breaker

```python
from enum import Enum

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
```

## Autenticación Avanzada

### OAuth 2.0 con Auto-Refresh

```python
@singleton
class OAuth2Manager:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.expires_at = 0

    async def get_token(self, http: Http) -> str:
        if time.time() < self.expires_at:
            return self.access_token

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
```

## Caching de Responses

```python
@singleton
class ResponseCache:
    def __init__(self):
        self._cache: dict[str, tuple[float, Any]] = {}
        self.ttl = 300  # 5 minutos

    def get(self, url: str) -> Any | None:
        if url in self._cache:
            ts, value = self._cache[url]
            if time.time() - ts < self.ttl:
                return value
        return None

    def set(self, url: str, value: Any):
        self._cache[url] = (time.time(), value)

@inject
async def cached_get(http: Http, cache: ResponseCache):
    cached = cache.get(url)
    if cached:
        return cached

    result = await http.get(url)
    data = result.to(dict)
    cache.set(url, data)
    return data
```

## Próximos Pasos

- [Result Pattern](result.md) - Manejo de respuestas y errores
- [Basic Usage](basic-usage.md) - Uso básico del cliente
