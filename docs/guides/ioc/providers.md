# Providers y Scopes

Los providers determinan cómo y cuándo se crean las instancias de tus servicios.

## Scopes Disponibles

R5 proporciona tres scopes:

| Scope | Decorator | Comportamiento | Uso típico |
|-------|-----------|----------------|------------|
| **Singleton** | `@singleton` | Una instancia compartida | Servicios sin estado, configuración |
| **Factory** | `@factory` | Nueva instancia cada vez | Objetos con estado mutable |
| **Resource** | `@resource` | Instancia con lifecycle | Conexiones, archivos, recursos |

## Singleton

### Concepto

Una única instancia que se comparte en toda la aplicación.

```python
from R5.ioc import singleton, Container

@singleton
class ConfigService:
    def __init__(self):
        print("ConfigService created")
        self.settings = load_settings()

# Primera resolución: crea la instancia
config1 = Container.resolve(ConfigService)  # "ConfigService created"

# Siguientes resoluciones: retorna la misma instancia
config2 = Container.resolve(ConfigService)  # No print
config3 = Container.resolve(ConfigService)  # No print

assert config1 is config2 is config3  # True
```

### Cuándo usar Singleton

✅ **Usar cuando:**
- El servicio no tiene estado mutable
- Quieres compartir una instancia entre toda la app
- El servicio es costoso de crear (conexiones, parsers)
- Necesitas consistencia (configuración, caché)

❌ **No usar cuando:**
- El objeto tiene estado que cambia entre requests
- Necesitas instancias independientes
- El objeto debe ser garbage collected

### Ejemplos

**Configuración:**
```python
@singleton
class AppConfig:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.api_key = os.getenv("API_KEY")
```

**Logger:**
```python
@singleton
class Logger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def info(self, message: str):
        self.logger.info(message)
```

**Caché:**
```python
@singleton
class CacheService:
    def __init__(self):
        self._cache: dict[str, Any] = {}
    
    def get(self, key: str) -> Any:
        return self._cache.get(key)
    
    def set(self, key: str, value: Any):
        self._cache[key] = value
```

**Service Layer:**
```python
@singleton
class UserRepository:
    def find(self, user_id: int):
        return query_db(f"SELECT * FROM users WHERE id = {user_id}")

@singleton
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
    
    def get_user(self, user_id: int):
        return self.repo.find(user_id)
```

## Factory

### Concepto

Crea una nueva instancia en cada resolución.

```python
from R5.ioc import factory, Container
from datetime import datetime
from uuid import uuid4

@factory
class RequestContext:
    def __init__(self):
        self.id = uuid4()
        self.timestamp = datetime.now()

ctx1 = Container.resolve(RequestContext)
ctx2 = Container.resolve(RequestContext)

assert ctx1 is not ctx2  # True
assert ctx1.id != ctx2.id  # True
```

### Cuándo usar Factory

✅ **Usar cuando:**
- Cada instancia debe ser independiente
- El objeto tiene estado mutable
- Necesitas valores únicos (IDs, timestamps)
- El objeto representa una operación o transacción

❌ **No usar cuando:**
- Quieres compartir estado
- La creación es muy costosa
- No hay razón para múltiples instancias

### Ejemplos

**Request Context:**
```python
@factory
class RequestContext:
    def __init__(self):
        self.request_id = uuid4()
        self.user_id: Optional[int] = None
        self.metadata: dict[str, Any] = {}
```

**Command Objects:**
```python
@factory
class CreateUserCommand:
    def __init__(self):
        self.username: str = ""
        self.email: str = ""
        self.timestamp = datetime.now()
    
    def execute(self):
        # Create user logic
        pass
```

**DTOs (Data Transfer Objects):**
```python
@factory
class UserDTO:
    def __init__(self):
        self.id: int = 0
        self.name: str = ""
        self.email: str = ""
```

**Builders:**
```python
@factory
class QueryBuilder:
    def __init__(self):
        self.query = ""
        self.params: list[Any] = []
    
    def where(self, condition: str, *params):
        self.query += f" WHERE {condition}"
        self.params.extend(params)
        return self
    
    def build(self):
        return (self.query, self.params)
```

## Resource

### Concepto

Instancia con lifecycle management usando async context manager.

```python
from R5.ioc import resource

@resource
class DatabaseConnection:
    async def __aenter__(self):
        print("Opening connection")
        self.conn = await create_connection()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("Closing connection")
        await self.conn.close()

@inject
async def query_users(db: DatabaseConnection):
    # db ya está en estado __aenter__
    users = await db.conn.query("SELECT * FROM users")
    return users
    # Al salir, se llama __aexit__ automáticamente
```

### Cuándo usar Resource

✅ **Usar cuando:**
- El objeto necesita inicialización asíncrona
- Requiere cleanup al terminar (close, dispose)
- Gestiona recursos del sistema (archivos, conexiones)
- Debe garantizar liberación de recursos

❌ **No usar cuando:**
- No hay recursos que liberar
- La inicialización es síncrona
- No necesitas async context manager

### Ejemplos

**Database Session:**
```python
@resource
class DatabaseSession:
    async def __aenter__(self):
        self.session = await create_async_session()
        await self.session.begin()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()

@inject
async def create_user(db: DatabaseSession, username: str):
    user = User(username=username)
    await db.session.add(user)
    # Commit automático al salir
```

**File Handler:**
```python
@resource
class FileHandler:
    def __init__(self, filename: str = "data.txt"):
        self.filename = filename
        self.file = None
    
    async def __aenter__(self):
        self.file = open(self.filename, "w")
        return self
    
    async def __aexit__(self, *args):
        if self.file:
            self.file.close()

@inject
async def write_logs(handler: FileHandler):
    handler.file.write("Log entry\n")
```

**HTTP Client:**
```python
@resource
class ApiClient:
    async def __aenter__(self):
        self.client = httpx.AsyncClient()
        return self
    
    async def __aexit__(self, *args):
        await self.client.aclose()
    
    async def get(self, url: str):
        return await self.client.get(url)

@inject
async def fetch_data(api: ApiClient):
    response = await api.get("https://api.example.com/data")
    return response.json()
```

## Decorador `component`

Para casos avanzados, usa `component` directamente:

```python
from R5.ioc import component, Scope

@component(scope=Scope.SINGLETON)
class MyService:
    pass

@component(scope=Scope.FACTORY)
class MyFactory:
    pass

@component(scope=Scope.RESOURCE)
class MyResource:
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass
```

## Registro Manual

Para casos donde no puedes usar decoradores:

```python
from R5.ioc import Container, Scope

class ThirdPartyService:
    pass

# Registrar manualmente
Container.registry_provider(ThirdPartyService, Scope.SINGLETON)

# Ahora se puede inyectar
@inject
def handler(service: ThirdPartyService):
    pass
```

## Scope con Dependencias

Los scopes se aplican al servicio, no a sus dependencias:

```python
@singleton
class Logger:
    pass

@factory
class Request:
    def __init__(self, logger: Logger):
        self.logger = logger  # Singleton inyectado
        self.id = uuid4()

# Cada Request es nueva instancia
req1 = Container.resolve(Request)
req2 = Container.resolve(Request)

# Pero comparten el mismo Logger
assert req1.logger is req2.logger  # True
assert req1 is not req2  # True
```

## Warnings de Sobreescritura

Si registras el mismo tipo dos veces, R5 emite un warning:

```python
@singleton
class MyService:
    pass

# Segunda vez - Warning!
@singleton
class MyService:  # UserWarning: Provider for type 'MyService' is being overwritten
    pass
```

Útil para detectar duplicados accidentales.

## Comparación de Scopes

```python
from uuid import uuid4

@singleton
class SingletonService:
    def __init__(self):
        self.id = uuid4()

@factory
class FactoryService:
    def __init__(self):
        self.id = uuid4()

# Singleton: mismo ID
s1 = Container.resolve(SingletonService)
s2 = Container.resolve(SingletonService)
assert s1.id == s2.id

# Factory: diferentes IDs
f1 = Container.resolve(FactoryService)
f2 = Container.resolve(FactoryService)
assert f1.id != f2.id
```

## Patrones Avanzados

### Lazy Singleton

```python
@singleton
class HeavyService:
    _instance = None
    
    def __init__(self):
        if HeavyService._instance is None:
            print("Initializing heavy service...")
            # Operaciones costosas
            HeavyService._instance = self

# No se crea hasta que se resuelve
service = Container.resolve(HeavyService)
```

### Factory con Configuración

```python
@singleton
class Config:
    def __init__(self):
        self.max_retries = 3

@factory
class RetryHandler:
    def __init__(self, config: Config):
        self.max_retries = config.max_retries
        self.attempts = 0

# Cada RetryHandler recibe config singleton
handler = Container.resolve(RetryHandler)
```

### Resource Pool

```python
@resource
class ConnectionPool:
    async def __aenter__(self):
        self.pool = await create_pool(size=10)
        return self
    
    async def __aexit__(self, *args):
        await self.pool.close()
    
    async def acquire(self):
        return await self.pool.acquire()
```

## Testing con Scopes

### Mock Singleton

```python
def test_service():
    Container.reset()
    
    @singleton
    class MockLogger:
        def log(self, msg):
            print(f"MOCK: {msg}")
    
    Container.alias_provider(Logger, MockLogger)
    
    # Tests usan MockLogger
```

### Factory para Tests

```python
@factory
class TestContext:
    def __init__(self):
        self.user_id = 999
        self.is_test = True

# Cada test obtiene nuevo contexto
def test_feature_1():
    ctx = Container.resolve(TestContext)
    assert ctx.is_test
```

## Próximos Pasos

- [Configuration](configuration.md) - Sistema de configuración
- [Injection](injection.md) - Guía de `@inject`
- [API Reference](../../api/ioc.md) - Documentación completa
