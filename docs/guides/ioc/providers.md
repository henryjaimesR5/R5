# Providers y Scopes

Los scopes determinan cómo y cuándo se crean las instancias.

## Resumen

| Scope | Decorator | Comportamiento | Uso típico |
|---|---|---|---|
| **Singleton** | `@singleton` | Una instancia compartida | Servicios, configuración, caché |
| **Factory** | `@factory` | Nueva instancia cada vez | Contextos, DTOs, commands |
| **Resource** | `@resource` | Instancia con lifecycle (`__aenter__`/`__aexit__`) | Conexiones, archivos, sesiones |

## Singleton

```python
from R5.ioc import singleton, Container

@singleton
class ConfigService:
    def __init__(self):
        self.settings = load_settings()

config1 = Container.resolve(ConfigService)
config2 = Container.resolve(ConfigService)
assert config1 is config2  # Misma instancia
```

## Factory

```python
from R5.ioc import factory
from uuid import uuid4

@factory
class RequestContext:
    def __init__(self):
        self.id = uuid4()
        self.timestamp = datetime.now()

ctx1 = Container.resolve(RequestContext)
ctx2 = Container.resolve(RequestContext)
assert ctx1 is not ctx2      # Instancias diferentes
assert ctx1.id != ctx2.id
```

## Resource

Requiere implementar `__aenter__` y `__aexit__`:

```python
from R5.ioc import resource

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
async def query_users(db: DatabaseSession):
    # db ya pasó por __aenter__
    users = await db.session.query("SELECT * FROM users")
    return users
    # __aexit__ se ejecuta automáticamente
```

## Scope con Dependencias

Los scopes se aplican al servicio, no a sus dependencias:

```python
@singleton
class Logger: pass

@factory
class Request:
    def __init__(self, logger: Logger):
        self.logger = logger  # Singleton compartido
        self.id = uuid4()

req1 = Container.resolve(Request)
req2 = Container.resolve(Request)
assert req1 is not req2              # Factory: diferentes
assert req1.logger is req2.logger    # Singleton: mismo
```

## Decorador genérico `component`

```python
from R5.ioc import component, Scope

@component(scope=Scope.SINGLETON)
class MyService: pass

@component(scope=Scope.FACTORY)
class MyFactory: pass
```

## Registro Manual

Para clases de terceros sin acceso al decorador:

```python
Container.registry_provider(ThirdPartyService, Scope.SINGLETON)
```

## Warnings de Sobreescritura

Registrar el mismo tipo dos veces emite un `UserWarning`:

```python
@singleton
class MyService: pass

@singleton
class MyService: pass  # ⚠️ UserWarning: Provider for 'MyService' is being overwritten
```

## Testing

```python
def test_service():
    Container.reset()

    class MockLogger:
        def log(self, msg): pass

    Container.registry_provider(MockLogger, Scope.SINGLETON)
    Container.alias_provider(Logger, MockLogger)
    # Tests usan MockLogger
```

## Próximos Pasos

- [Injection](injection.md) - `@inject` decorator
- [Configuration](configuration.md) - `@config` y formatos
