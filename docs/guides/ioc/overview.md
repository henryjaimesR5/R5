# IoC Container - Overview

El contenedor de Inversión de Control (IoC) gestiona la creación y resolución de dependencias automáticamente usando type hints.

## Beneficios

```python
# Sin IoC: dependencias manuales
class UserService:
    def __init__(self):
        self.db = DatabaseConnection()
        self.cache = CacheService()

# Con IoC: inyección automática
@singleton
class UserService:
    def __init__(self, db: DatabaseConnection, cache: CacheService):
        self.db = db
        self.cache = cache
```

- **Desacoplamiento** - Las clases no crean sus dependencias
- **Testing** - Reemplazar dependencias con mocks es trivial
- **Type-safe** - Resolución automática via type hints

## Componentes

| Componente | Descripción |
|---|---|
| `Container` | Registro central de providers |
| `@singleton` / `@factory` / `@resource` | Decoradores de scope ([detalle](providers.md)) |
| `@inject` | Inyecta dependencias en funciones ([detalle](injection.md)) |
| `@config` | Carga configuración desde archivos ([detalle](configuration.md)) |

## Ejemplo Rápido

```python
from R5.ioc import singleton, inject, Container

@singleton
class Logger:
    def log(self, msg: str):
        print(msg)

@singleton
class UserService:
    def __init__(self, logger: Logger):
        self.logger = logger

@inject
async def handler(service: UserService, user_id: int):
    service.logger.log(f"Processing {user_id}")

await handler(user_id=123)
```

## Container API

```python
# Registrar manualmente
Container.registry_provider(MyService, Scope.SINGLETON)

# Verificar existencia
Container.in_provider(MyService)  # True/False

# Resolver instancia
instance = Container.resolve(MyService)

# Alias (interfaces)
Container.alias_provider(IRepository, PostgresRepository)

# Snapshot/Restore (útil en tests)
snapshot = Container.snapshot()
Container.restore(snapshot)

# Reset completo
Container.reset()
```

## Resolución de Dependencias

R5 resuelve cadenas de dependencias automáticamente y detecta ciclos:

```python
@singleton
class Logger: pass

@singleton
class Cache:
    def __init__(self, logger: Logger): ...

@singleton
class UserService:
    def __init__(self, cache: Cache, logger: Logger): ...

# Resuelve: UserService → Cache → Logger
user_service = Container.resolve(UserService)
```

```python
# Dependencia circular → CircularDependencyError
@singleton
class A:
    def __init__(self, b: 'B'): ...

@singleton
class B:
    def __init__(self, a: A): ...
```

## Debugging

```python
from R5.ioc.errors import ProviderNotFoundError, CircularDependencyError

try:
    Container.resolve(UnknownService)
except ProviderNotFoundError as e:
    print(f"Not found: {e.provider_type}")
    print(f"Available: {e.available_providers}")
```

## Próximos Pasos

- [Injection](injection.md) - Guía completa de `@inject`
- [Providers](providers.md) - Scopes: singleton, factory, resource
- [Configuration](configuration.md) - `@config` y formatos soportados
