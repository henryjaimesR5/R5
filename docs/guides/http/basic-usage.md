# HTTP Client - Uso Básico

## Setup

El cliente HTTP se inyecta automáticamente via IoC:

```python
from R5.http import Http
from R5.ioc import inject

@inject
async def my_function(http: Http):
    result = await http.get("https://api.example.com/data")
    return result
```

## GET Requests

```python
@inject
async def fetch_data(http: Http):
    # Simple
    result = await http.get("https://api.example.com/users/1")

    # Con query params, headers y timeout
    result = await http.get(
        "https://api.example.com/users",
        params={"page": 1, "limit": 10, "sort": "name:asc"},
        headers={
            "Authorization": "Bearer eyJhbGc...",
            "Accept": "application/json"
        },
        timeout=5.0
    )
```

## POST Requests

```python
@inject
async def create_data(http: Http):
    # JSON
    result = await http.post(
        "https://api.example.com/users",
        json={"name": "John Doe", "email": "john@example.com"}
    )

    # Form data
    result = await http.post(
        "https://api.example.com/form",
        data={"username": "johndoe", "password": "secret123"}
    )
    # Content-Type: application/x-www-form-urlencoded

    # Bytes (upload)
    with open("image.jpg", "rb") as f:
        result = await http.post(
            "https://api.example.com/upload",
            content=f.read(),
            headers={"Content-Type": "image/jpeg"}
        )
```

## PUT / PATCH / DELETE

```python
@inject
async def other_methods(http: Http):
    # PUT - reemplazo completo
    result = await http.put(
        "https://api.example.com/users/1",
        json={"name": "Jane Doe", "email": "jane@example.com"}
    )

    # PATCH - actualización parcial
    result = await http.patch(
        "https://api.example.com/users/1",
        json={"email": "newemail@example.com"}
    )

    # DELETE
    result = await http.delete("https://api.example.com/users/1")
```

## Mapeo a DTOs

```python
from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class User:
    id: int
    name: str
    email: str

@inject
async def get_user(http: Http):
    result = await http.get("https://jsonplaceholder.typicode.com/users/1")

    user = result.to(User)       # Dataclass o Pydantic BaseModel
    data = result.to(dict)       # Dict
    items = result.to(list)      # List

    if user:
        print(f"Name: {user.name}")
```

Ver [Result Pattern](result.md) para detalles sobre `to()`, handlers y manejo de errores.

## Handlers por Request

```python
@inject
async def with_handlers(http: Http):
    result = await http.get(
        "https://api.example.com/users/1",
        on_before=lambda req: print(f"→ {req.method} {req.url}"),
        on_after=lambda req, res: print(f"← {res.status_code}"),
        on_status={
            200: lambda: print("Success"),
            404: lambda: print("Not found")
        },
        on_exception=lambda e: print(f"Error: {e}")
    )
```

Para handlers globales (todas las requests), ver [Advanced](advanced.md#handlers-globales).

## Requests Concurrentes

```python
import asyncio

@inject
async def fetch_multiple(http: Http):
    results = await asyncio.gather(
        http.get("https://api.example.com/users/1"),
        http.get("https://api.example.com/users/2"),
        http.get("https://api.example.com/users/3")
    )

    users = [r.to(User) for r in results if r.status == 200]
    return users
```

## Ejemplo: CRUD Completo

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Todo:
    id: Optional[int]
    title: str
    completed: bool = False

@inject
async def crud(http: Http):
    base = "https://jsonplaceholder.typicode.com/todos"

    # CREATE
    created = (await http.post(base, json={"title": "New", "completed": False})).to(Todo)

    # READ
    todo = (await http.get(f"{base}/1")).to(Todo)

    # UPDATE
    updated = (await http.put(f"{base}/1", json={"title": "Updated", "completed": True})).to(Todo)

    # DELETE
    delete_result = await http.delete(f"{base}/1")
    print(f"Deleted: {delete_result.status}")
```

## Paginación

```python
@inject
async def fetch_all_pages(http: Http):
    all_users = []
    page = 1

    while True:
        result = await http.get(
            "https://api.example.com/users",
            params={"page": page, "limit": 10}
        )

        if result.status != 200:
            break

        users = result.to(list)
        if not users:
            break

        all_users.extend(users)
        page += 1

    return all_users
```

## Manejo de Errores

```python
@inject
async def handle_errors(http: Http):
    result = await http.get("https://api.example.com/data")

    if result.exception:
        print(f"Error de red: {result.exception}")
        return None

    data = result.to(dict)  # None si falla el parsing JSON
    if data is None:
        print("JSON inválido")
        return {}

    return data
```

## Próximos Pasos

- [Advanced Features](advanced.md) - Retry, proxy rotation, handlers globales
- [Result Pattern](result.md) - Manejo avanzado de respuestas
