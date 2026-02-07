# Ejemplos Simples

Ejemplos básicos para empezar con R5. Para detalles de cada módulo, consulta las guías específicas.

## IoC - Hello World

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

## HTTP - Fetch y Mapeo a DTO

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

## Background - Tareas en Paralelo

```python
import asyncio
from R5.background import Background
from R5.ioc import inject

def process(item_id: int):
    print(f"Processing {item_id}")

@inject
async def main(bg: Background):
    for i in range(5):
        await bg.add(process, i)
    await asyncio.sleep(1)

asyncio.run(main())
```

## Configuration

```python
from R5.ioc import config, inject

@config(file='.env')
class AppConfig:
    app_name: str = "MyApp"
    port: int = 3000
    debug: bool = False

@inject
async def main(cfg: AppConfig):
    print(f"{cfg.app_name} on port {cfg.port}")
```

## Requests Concurrentes

```python
import asyncio
from R5.http import Http
from R5.ioc import inject

@inject
async def main(http: Http):
    results = await asyncio.gather(*[
        http.get(f"https://jsonplaceholder.typicode.com/users/{i}")
        for i in range(1, 4)
    ])
    for r in results:
        user = r.to(dict)
        if user:
            print(user["name"])

asyncio.run(main())
```

## Guías detalladas

- [IoC Container](../guides/ioc/overview.md) - Inyección de dependencias
- [HTTP Client](../guides/http/overview.md) - Cliente HTTP
- [Background Tasks](../guides/background/overview.md) - Tareas concurrentes
- [Patrones](patterns.md) - Patrones de diseño con R5
- [Ejemplos reales](real-world.md) - Aplicaciones completas
