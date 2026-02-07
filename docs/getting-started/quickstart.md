# Quick Start

Aprende los fundamentos de R5 en 5 minutos.

## Tu primera aplicación

```python
import asyncio
from R5.ioc import singleton, inject

@singleton
class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"

@inject
async def main(service: GreetingService):
    print(service.greet("World"))

asyncio.run(main())
```

```bash
uv run python app.py
# Output: Hello, World!
```

## Con HTTP Client

```python
import asyncio
from dataclasses import dataclass
from R5.http import Http
from R5.ioc import inject

@dataclass
class User:
    id: int
    name: str
    email: str

@inject
async def main(http: Http):
    user = (await http.get("https://jsonplaceholder.typicode.com/users/1")).to(User)
    if user:
        print(f"{user.name} ({user.email})")

asyncio.run(main())
```

## Ejemplo Completo (IoC + HTTP + Background)

```python
import asyncio
from dataclasses import dataclass
from R5.ioc import singleton, inject, config
from R5.http import Http
from R5.background import Background

@config(file='.env')
class AppConfig:
    api_url: str = "https://jsonplaceholder.typicode.com"

@singleton
class Logger:
    def log(self, msg: str): print(f"[LOG] {msg}")

@dataclass
class Post:
    id: int
    title: str
    userId: int

@inject
async def main(config: AppConfig, http: Http, bg: Background, log: Logger):
    log.log("Started")

    post = (await http.get(f"{config.api_url}/posts/1")).to(Post)
    if post:
        log.log(f"Fetched: {post.title}")
        await bg.add(lambda: log.log(f"Processing post #{post.id}"))

    await asyncio.sleep(0.3)
    log.log("Done")

asyncio.run(main())
```

## Estructura de proyecto recomendada

```
my_project/
├── app/
│   ├── services/
│   │   ├── user_service.py
│   │   └── email_service.py
│   ├── config.py
│   └── main.py
├── tests/
├── .env
└── pyproject.toml
```

## Siguientes pasos

- [Core Concepts](core-concepts.md) - Arquitectura del framework
- [IoC Container](../guides/ioc/overview.md) - Dependency injection
- [HTTP Client](../guides/http/overview.md) - Cliente HTTP
- [Background Tasks](../guides/background/overview.md) - Tareas concurrentes
