# Dependency Injection

El decorador `@inject` es la forma principal de usar el contenedor IoC en R5.

## Uso Básico

```python
from R5.ioc import singleton, inject

@singleton
class EmailService:
    def send(self, to: str, message: str):
        print(f"Sending to {to}: {message}")

@inject
def send_welcome_email(email_service: EmailService, user_email: str):
    email_service.send(user_email, "Welcome!")

send_welcome_email(user_email="user@example.com")
```

## Cómo Funciona

`@inject` analiza la firma de la función y:

1. Identifica parámetros con type hints
2. Verifica si el tipo está registrado en el container
3. Resuelve automáticamente las dependencias
4. Inyecta las instancias en la llamada a la función

```python
@inject
def handler(
    service_a: ServiceA,  # ✅ Inyectado automáticamente
    service_b: ServiceB,  # ✅ Inyectado automáticamente
    user_id: int,         # ⚠️  Parámetro normal (no registrado)
    name: str = "John"    # ⚠️  Parámetro con default
):
    pass

# Solo pasas los parámetros no inyectables
handler(user_id=123, name="Alice")
```

## Funciones Síncronas

```python
@singleton
class LogService:
    def log(self, message: str):
        print(f"[LOG] {message}")

@inject
def process_sync(log: LogService, data: str):
    log.log(f"Processing: {data}")
    return data.upper()

result = process_sync(data="hello")
```

## Funciones Asíncronas

```python
@singleton
class DatabaseService:
    async def query(self, sql: str):
        return [{"id": 1, "name": "John"}]

@inject
async def fetch_users(db: DatabaseService):
    users = await db.query("SELECT * FROM users")
    return users

users = await fetch_users()
```

## Múltiples Dependencias

```python
@singleton
class CacheService:
    def get(self, key: str):
        return f"cached:{key}"

@singleton
class LogService:
    def log(self, msg: str):
        print(f"[LOG] {msg}")

@singleton
class EmailService:
    def send(self, to: str):
        print(f"Email to {to}")

@inject
def complex_handler(
    cache: CacheService,
    log: LogService,
    email: EmailService,
    user_id: int
):
    log.log(f"Processing user {user_id}")
    data = cache.get(f"user:{user_id}")
    email.send("admin@example.com")
    return data

result = complex_handler(user_id=42)
```

## Parámetros Keyword-Only

Después del primer parámetro inyectable, los parámetros no inyectables se convierten en **keyword-only**:

```python
@singleton
class MyService:
    pass

@inject
def handler(service: MyService, user_id: int, name: str):
    pass

# ✅ Correcto
handler(user_id=1, name="John")

# ❌ Error: user_id y name deben ser keyword
handler(1, "John")
```

Esto previene errores de orden de argumentos.

### Ejemplo del cambio de signature

```python
import inspect

@singleton
class ServiceA:
    pass

@inject
def handler(service: ServiceA, param1: str, param2: int):
    return (param1, param2)

sig = inspect.signature(handler)
print(sig)
# (service: ServiceA, *, param1: str, param2: int)
#                      ^
#                      Nota el asterisco: keyword-only
```

## Dependencias Opcionales

Usa `Optional` para dependencias que pueden no estar registradas:

```python
from typing import Optional
from R5.ioc import singleton, inject

@singleton
class CacheService:
    pass

@inject
def handler(
    cache: Optional[CacheService],
    data: str
):
    if cache:
        cache.set("key", data)
    return data

# Funciona incluso si CacheService no está registrado
handler(data="test")
```

## Inyección en Métodos de Clase

```python
@singleton
class EmailService:
    def send(self, to: str):
        print(f"Email to {to}")

class UserController:
    @inject
    def create_user(self, email_service: EmailService, username: str):
        email_service.send("admin@example.com")
        return f"Created user: {username}"

controller = UserController()
result = controller.create_user(username="john_doe")
```

## Inyección en Constructores

Para inyectar en `__init__`, usa el decorador en la clase:

```python
@singleton
class LogService:
    def log(self, msg: str):
        print(msg)

@singleton
class UserService:
    def __init__(self, log: LogService):
        self.log = log
    
    def create_user(self, name: str):
        self.log.log(f"Creating user: {name}")

# R5 inyecta LogService automáticamente en __init__
user_service = Container.resolve(UserService)
user_service.create_user("John")
```

## Inyección Anidada

Las dependencias pueden tener sus propias dependencias:

```python
@singleton
class Logger:
    def log(self, msg: str):
        print(msg)

@singleton
class Cache:
    def __init__(self, logger: Logger):
        self.logger = logger

@singleton
class UserRepository:
    def __init__(self, cache: Cache, logger: Logger):
        self.cache = cache
        self.logger = logger

@inject
def get_user(repo: UserRepository, user_id: int):
    return repo.find(user_id)

# R5 resuelve toda la cadena: UserRepository -> Cache -> Logger
user = get_user(user_id=1)
```

## Scope Mixing

Puedes mezclar diferentes scopes:

```python
@singleton
class ConfigService:
    pass

@factory
class RequestContext:
    def __init__(self):
        self.id = uuid4()

@inject
def handle_request(
    config: ConfigService,      # Singleton
    context: RequestContext,    # Factory (nueva instancia)
    data: str
):
    print(f"Request {context.id}")
    return data

# Cada llamada recibe el mismo config pero nuevo context
handle_request(data="test1")
handle_request(data="test2")
```

## Resource Injection

Cuando inyectas un `@resource`, R5 gestiona automáticamente el lifecycle:

```python
@resource
class DatabaseSession:
    async def __aenter__(self):
        print("Opening DB session")
        self.session = create_session()
        return self
    
    async def __aexit__(self, *args):
        print("Closing DB session")
        await self.session.close()

@inject
async def query_users(db: DatabaseSession):
    # db ya está en estado __aenter__
    users = await db.session.query("SELECT * FROM users")
    return users
    # Al salir, se llama __aexit__ automáticamente

users = await query_users()
```

## Errores Comunes

### 1. Tipo no registrado

```python
class UnregisteredService:
    pass

@inject
def handler(service: UnregisteredService):
    pass

# ❌ ProviderNotFoundError
handler()
```

**Solución:** Registra el servicio con `@singleton`, `@factory` o `@resource`.

### 2. Dependencia circular

```python
@singleton
class ServiceA:
    def __init__(self, service_b: 'ServiceB'):
        pass

@singleton
class ServiceB:
    def __init__(self, service_a: ServiceA):
        pass

# ❌ CircularDependencyError
Container.resolve(ServiceA)
```

**Solución:** Refactoriza para eliminar el ciclo o usa lazy loading.

### 3. Type hint faltante

```python
@singleton
class MyService:
    pass

@inject
def handler(service):  # ❌ Sin type hint
    pass
```

**Solución:** Agrega type hints:

```python
@inject
def handler(service: MyService):  # ✅
    pass
```

### 4. Mezclar posicional y keyword

```python
@singleton
class MyService:
    pass

@inject
def handler(service: MyService, user_id: int):
    pass

# ❌ Error: user_id debe ser keyword-only
handler(123)

# ✅ Correcto
handler(user_id=123)
```

## Patterns Avanzados

### Conditional Injection

```python
from typing import Optional

@inject
def handler(cache: Optional[CacheService], data: str):
    if cache:
        return cache.get(data)
    return fetch_from_db(data)
```

### Multiple Implementations

```python
@singleton
class PostgresRepository:
    pass

@singleton
class MongoRepository:
    pass

# Registrar alias según configuración
if config.database == "postgres":
    Container.alias_provider(IRepository, PostgresRepository)
else:
    Container.alias_provider(IRepository, MongoRepository)

@inject
def get_data(repo: IRepository):
    return repo.find_all()
```

### Partial Injection

```python
@singleton
class EmailService:
    pass

@inject
def send_email(
    email_service: EmailService,
    to: str,
    subject: str,
    body: str
):
    email_service.send(to, subject, body)

# Crear función parcial
from functools import partial
send_welcome = partial(
    send_email,
    subject="Welcome!",
    body="Thanks for joining"
)

# Usar
send_welcome(to="user@example.com")
```

## Testing

### Mock Dependencies

```python
import pytest
from R5.ioc import Container, Scope

@singleton
class EmailService:
    def send(self, to: str):
        # Real implementation
        pass

def test_handler():
    Container.reset()
    
    # Mock service
    class MockEmailService:
        def send(self, to: str):
            print(f"Mock: sending to {to}")
    
    Container.registry_provider(MockEmailService, Scope.SINGLETON)
    Container.alias_provider(EmailService, MockEmailService)
    
    @inject
    def handler(email: EmailService):
        email.send("test@example.com")
    
    handler()  # Usa MockEmailService
```

### Fixture con dependencias

```python
@pytest.fixture
def clean_container():
    snapshot = Container.snapshot()
    yield
    Container.restore(snapshot)

def test_with_clean_container(clean_container):
    @singleton
    class TestService:
        pass
    
    # Test logic...
```

## Próximos Pasos

- [Providers](providers.md) - Decoradores de scope
- [Configuration](configuration.md) - Sistema de configuración
- [API Reference](../../api/ioc.md) - Documentación completa de la API
