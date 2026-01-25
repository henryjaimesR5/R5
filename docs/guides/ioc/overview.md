# IoC Container - Overview

El contenedor de Inversión de Control (IoC) es el corazón de R5, proporcionando inyección de dependencias automática y type-safe.

## ¿Qué es IoC?

**Inversión de Control (IoC)** es un patrón de diseño donde el control del flujo de la aplicación se invierte: en lugar de que tu código cree y gestione dependencias manualmente, el framework lo hace por ti.

## Beneficios

### ✅ Código más limpio

**Sin IoC:**
```python
class UserService:
    def __init__(self):
        self.db = DatabaseConnection()
        self.cache = CacheService()
        self.logger = Logger()

class OrderService:
    def __init__(self):
        self.user_service = UserService()
        self.email = EmailService()
```

**Con IoC:**
```python
@singleton
class UserService:
    def __init__(self, db: DatabaseConnection, cache: CacheService, logger: Logger):
        self.db = db
        self.cache = cache
        self.logger = logger

@singleton
class OrderService:
    def __init__(self, user_service: UserService, email: EmailService):
        self.user_service = user_service
        self.email = email
```

### ✅ Testing más fácil

```python
@inject
async def process_order(order_service: OrderService):
    await order_service.create_order(...)

# En tests, puedes reemplazar las dependencias
Container.reset()
Container.registry_provider(MockOrderService, Scope.SINGLETON)
Container.alias_provider(OrderService, MockOrderService)
```

### ✅ Type-safe

El container usa type hints para resolución automática:

```python
@inject
def handler(
    service: UserService,  # Resuelto automáticamente
    cache: CacheService,   # Resuelto automáticamente
    user_id: int           # Parámetro manual
):
    pass

handler(user_id=123)  # Solo pasas lo que no es inyectable
```

## Componentes Principales

### 1. Container

El contenedor central que almacena y resuelve dependencias:

```python
from R5.ioc import Container, Scope

# Registrar proveedor manualmente
Container.registry_provider(MyService, Scope.SINGLETON)

# Verificar si existe
if Container.in_provider(MyService):
    print("MyService está registrado")

# Resolver instancia
instance = Container.resolve(MyService)

# Obtener provider
provider = Container.get_provider(MyService)

# Crear alias
Container.alias_provider(IMyService, MyService)
```

### 2. Decoradores de Scope

R5 proporciona decoradores para registrar servicios:

```python
from R5.ioc import singleton, factory, resource

@singleton
class DatabaseConnection:
    pass

@factory
class Request:
    pass

@resource
class FileHandler:
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass
```

### 3. Inyección

El decorador `@inject` inyecta dependencias automáticamente:

```python
from R5.ioc import inject

@inject
async def handler(
    db: DatabaseConnection,
    cache: CacheService,
    user_id: int  # No se inyecta, es parámetro normal
):
    user = await db.find(user_id)
    cache.set(f"user:{user_id}", user)

await handler(user_id=123)
```

### 4. Configuration

Carga configuración desde archivos:

```python
from R5.ioc import config

@config(file='config.json')
class AppConfig:
    database_url: str = "sqlite:///db.sqlite"
    api_key: str = ""
    debug: bool = False
```

## Scopes (Alcances)

### Singleton

Una única instancia compartida en toda la aplicación:

```python
@singleton
class DatabaseConnection:
    def __init__(self):
        print("Creating DB connection")
        self.conn = create_connection()

# Primera llamada: crea instancia
db1 = Container.resolve(DatabaseConnection)  # "Creating DB connection"

# Segunda llamada: retorna misma instancia
db2 = Container.resolve(DatabaseConnection)  # No print

assert db1 is db2  # True
```

**Casos de uso:**
- Conexiones a base de datos
- Configuración
- Servicios sin estado
- Caché compartida

### Factory

Nueva instancia en cada resolución:

```python
@factory
class Request:
    def __init__(self):
        self.id = uuid4()
        self.timestamp = datetime.now()

req1 = Container.resolve(Request)
req2 = Container.resolve(Request)

assert req1 is not req2  # True
assert req1.id != req2.id  # True
```

**Casos de uso:**
- Objetos con estado mutable
- Request contexts
- Objetos temporales

### Resource

Instancia con lifecycle management (context manager):

```python
@resource
class FileHandler:
    async def __aenter__(self):
        print("Opening file")
        self.file = open("data.txt", "w")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("Closing file")
        self.file.close()

@inject
async def write_data(handler: FileHandler):
    # handler ya está en contexto __aenter__
    handler.file.write("data")
    # Al salir de la función, se llama __aexit__
```

**Casos de uso:**
- Archivos
- Conexiones de red
- Sesiones de base de datos
- Recursos que requieren cleanup

## Resolución de Dependencias

### Automática

```python
@singleton
class ServiceA:
    pass

@singleton
class ServiceB:
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a

# ServiceB automáticamente recibe ServiceA
instance = Container.resolve(ServiceB)
assert isinstance(instance.service_a, ServiceA)
```

### Cadena de Dependencias

```python
@singleton
class Logger:
    pass

@singleton
class Cache:
    def __init__(self, logger: Logger):
        self.logger = logger

@singleton
class UserService:
    def __init__(self, cache: Cache, logger: Logger):
        self.cache = cache
        self.logger = logger

# Resuelve toda la cadena
user_service = Container.resolve(UserService)
# UserService -> Cache -> Logger
# UserService -> Logger
```

### Detección de Ciclos

R5 detecta dependencias circulares:

```python
@singleton
class ServiceA:
    def __init__(self, service_b: 'ServiceB'):
        pass

@singleton
class ServiceB:
    def __init__(self, service_a: ServiceA):
        pass

# Lanza CircularDependencyError
Container.resolve(ServiceA)
```

## Gestión del Container

### Reset

Limpia todo el container:

```python
Container.reset()
```

Útil en tests:

```python
def test_my_service():
    Container.reset()
    
    @singleton
    class MockService:
        pass
    
    # Tests...
```

### Snapshot & Restore

Guarda y restaura el estado del container:

```python
# Guardar estado actual
snapshot = Container.snapshot()

# Hacer cambios
@singleton
class NewService:
    pass

# Restaurar estado anterior
Container.restore(snapshot)
```

## Alias

Crea alias para implementaciones concretas:

```python
from abc import ABC, abstractmethod

class IUserRepository(ABC):
    @abstractmethod
    def find(self, user_id: int):
        pass

@singleton
class PostgresUserRepository(IUserRepository):
    def find(self, user_id: int):
        return f"User from Postgres: {user_id}"

# Registrar alias
Container.alias_provider(IUserRepository, PostgresUserRepository)

# Usar interfaz
@inject
def get_user(repo: IUserRepository, user_id: int):
    return repo.find(user_id)

result = get_user(user_id=1)
```

## Debugging

### Ver providers registrados

```python
container = Container.get_container()
for provider_type, provider in container.items():
    print(f"{provider_type.__name__}: {provider}")
```

### Verificar si existe

```python
if Container.in_provider(MyService):
    print("MyService está registrado")
else:
    print("MyService NO está registrado")
```

### Manejo de errores

```python
from R5.ioc.errors import ProviderNotFoundError, CircularDependencyError

try:
    instance = Container.resolve(UnknownService)
except ProviderNotFoundError as e:
    print(f"Provider not found: {e.provider_type}")
    print(f"Available: {e.available_providers}")

try:
    instance = Container.resolve(CircularService)
except CircularDependencyError as e:
    print(f"Circular dependency: {e.dependency_chain}")
```

## Próximos Pasos

- [Dependency Injection](injection.md) - Guía completa de `@inject`
- [Providers](providers.md) - Scopes y decoradores
- [Configuration](configuration.md) - Sistema de configuración
