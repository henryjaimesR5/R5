# Dependency Injection

El decorador `@inject` resuelve e inyecta dependencias automáticamente basándose en type hints.

## Uso Básico

```python
from R5.ioc import singleton, inject

@singleton
class EmailService:
    def send(self, to: str, message: str):
        print(f"Sending to {to}: {message}")

@inject
def send_welcome(email_service: EmailService, user_email: str):
    email_service.send(user_email, "Welcome!")

send_welcome(user_email="user@example.com")
```

## Cómo Funciona

`@inject` analiza la firma, identifica tipos registrados en el container y los inyecta. Los parámetros no registrados se pasan manualmente:

```python
@inject
def handler(
    service_a: ServiceA,  # Inyectado automáticamente
    service_b: ServiceB,  # Inyectado automáticamente
    user_id: int,         # Parámetro manual (keyword-only)
    name: str = "John"    # Parámetro manual con default
):
    pass

handler(user_id=123)
```

Los parámetros no inyectables se convierten en **keyword-only** para prevenir errores de orden.

## Funciones Async

```python
@inject
async def fetch_users(db: DatabaseService):
    return await db.query("SELECT * FROM users")

users = await fetch_users()
```

## Múltiples Dependencias

```python
@inject
def handler(cache: CacheService, log: LogService, email: EmailService, user_id: int):
    log.log(f"Processing {user_id}")
    data = cache.get(f"user:{user_id}")
    email.send("admin@example.com")
    return data

result = handler(user_id=42)
```

## Inyección en Clases

```python
# En métodos
class UserController:
    @inject
    def create_user(self, email: EmailService, username: str):
        email.send("admin@example.com")
        return f"Created: {username}"

# En constructores (el scope decorator registra y resuelve __init__)
@singleton
class UserService:
    def __init__(self, logger: Logger, cache: Cache):
        self.logger = logger
        self.cache = cache
```

## Inyección Anidada

R5 resuelve cadenas de dependencias automáticamente:

```python
@singleton
class Logger: pass

@singleton
class Cache:
    def __init__(self, logger: Logger): ...

@singleton
class UserRepo:
    def __init__(self, cache: Cache, logger: Logger): ...

@inject
def get_user(repo: UserRepo, user_id: int):
    return repo.find(user_id)
# Resuelve: UserRepo → Cache → Logger
```

## Dependencias Opcionales

```python
from typing import Optional

@inject
def handler(cache: Optional[CacheService], data: str):
    if cache:
        return cache.get(data)
    return fetch_from_db(data)
```

## Resource Injection

`@resource` se gestiona automáticamente con context manager:

```python
@resource
class DatabaseSession:
    async def __aenter__(self):
        self.session = create_session()
        return self
    async def __aexit__(self, *args):
        await self.session.close()

@inject
async def query(db: DatabaseSession):
    # db ya pasó por __aenter__
    return await db.session.query("...")
    # __aexit__ se ejecuta al salir
```

## Errores Comunes

| Error | Causa | Solución |
|---|---|---|
| `ProviderNotFoundError` | Tipo no registrado | Decorar con `@singleton`/`@factory`/`@resource` |
| `CircularDependencyError` | A depende de B, B de A | Refactorizar para eliminar ciclo |
| Sin inyección | Falta type hint | Agregar: `def handler(service: MyService)` |
| `TypeError` en args | Parámetro posicional | Usar keyword: `handler(user_id=123)` |

## Alias para Interfaces

```python
Container.alias_provider(IUserRepository, PostgresUserRepository)

@inject
def get_data(repo: IUserRepository):
    return repo.find_all()
```

## Testing

```python
def test_handler():
    Container.reset()

    class MockEmail:
        def send(self, to): pass

    Container.registry_provider(MockEmail, Scope.SINGLETON)
    Container.alias_provider(EmailService, MockEmail)

    @inject
    def handler(email: EmailService):
        email.send("test@example.com")

    handler()  # Usa MockEmail
```

## Próximos Pasos

- [Providers](providers.md) - Scopes y decoradores
- [Configuration](configuration.md) - `@config`
