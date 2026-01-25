# Quick Start

Aprende los fundamentos de R5 en 5 minutos.

## Tu primera aplicación

Crea un archivo `app.py`:

```python
import asyncio
from R5.ioc import singleton, inject

@singleton
class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"

@inject
async def main(service: GreetingService):
    message = service.greet("World")
    print(message)

if __name__ == "__main__":
    asyncio.run(main())
```

Ejecuta:

```bash
uv run python app.py
# Output: Hello, World!
```

## Ejemplo con HTTP

Crea `http_app.py`:

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
    username: str

@inject
async def fetch_user(http: Http):
    result = await http.get("https://jsonplaceholder.typicode.com/users/1")
    user = result.to(User)
    
    if user:
        print(f"User: {user.name} ({user.email})")

if __name__ == "__main__":
    asyncio.run(fetch_user())
```

Ejecuta:

```bash
uv run python http_app.py
```

## Ejemplo con Background Tasks

Crea `background_app.py`:

```python
import asyncio
from R5.background import Background
from R5.ioc import singleton, inject

@singleton
class NotificationService:
    def notify(self, message: str):
        print(f"📧 Notification: {message}")

def send_email(to: str):
    print(f"✉️  Sending email to {to}")

@inject
async def main(bg: Background, notifier: NotificationService):
    await bg.add(send_email, "user@example.com")
    await bg.add(send_email, "admin@example.com")
    await bg.add(lambda: notifier.notify("Tasks completed"))
    
    await asyncio.sleep(0.5)
    print("All tasks queued!")

if __name__ == "__main__":
    asyncio.run(main())
```

Ejecuta:

```bash
uv run python background_app.py
```

## Ejemplo Completo

Combina todos los módulos en `complete_app.py`:

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
class LogService:
    def log(self, message: str):
        print(f"[LOG] {message}")

@dataclass
class Post:
    id: int
    title: str
    userId: int

@inject
async def main(
    config: AppConfig,
    http: Http,
    bg: Background,
    log: LogService
):
    log.log("Application started")
    
    result = await http.get(f"{config.api_url}/posts/1")
    post = result.to(Post)
    
    if post:
        log.log(f"Fetched post: {post.title}")
        
        await bg.add(
            lambda: log.log(f"Processing post #{post.id}")
        )
        
        await asyncio.sleep(0.3)
    
    log.log("Application finished")

if __name__ == "__main__":
    asyncio.run(main())
```

Crea `.env`:

```env
API_URL=https://jsonplaceholder.typicode.com
```

Ejecuta:

```bash
uv run python complete_app.py
```

## Estructura de proyecto recomendada

```
my_project/
├── app/
│   ├── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   └── email_service.py
│   ├── config.py
│   └── main.py
├── tests/
│   └── test_services.py
├── .env
├── .env.example
├── pyproject.toml
└── README.md
```

### `app/config.py`

```python
from R5.ioc import config

@config(file='.env')
class AppConfig:
    database_url: str = "sqlite:///app.db"
    api_key: str = ""
    debug: bool = False
```

### `app/services/user_service.py`

```python
from R5.ioc import singleton
from R5.http import Http

@singleton
class UserService:
    def __init__(self, http: Http):
        self._http = http
    
    async def get_user(self, user_id: int):
        result = await self._http.get(f"/users/{user_id}")
        return result.to(dict)
```

### `app/main.py`

```python
import asyncio
from R5.ioc import inject
from app.services.user_service import UserService
from app.config import AppConfig

@inject
async def main(config: AppConfig, user_service: UserService):
    if config.debug:
        print("Debug mode enabled")
    
    user = await user_service.get_user(1)
    print(f"User: {user}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Siguientes pasos

Ahora que has visto los ejemplos básicos:

- Lee [Core Concepts](core-concepts.md) para entender la arquitectura
- Explora las [Guías de IoC](../guides/ioc/overview.md) para dependency injection avanzada
- Revisa las [Guías de HTTP](../guides/http/overview.md) para cliente HTTP
- Consulta [Ejemplos avanzados](../examples/real-world.md) para casos reales
