# HTTP Client - Uso Básico

Guía práctica para usar el cliente HTTP de R5.

## Setup Inicial

```python
from R5.http import Http
from R5.ioc import inject

@inject
async def my_function(http: Http):
    # http ya está disponible con connection pooling
    result = await http.get("https://api.example.com/data")
    return result
```

El cliente HTTP se inyecta automáticamente. No necesitas crear instancias manualmente.

## GET Requests

### Simple GET

```python
@inject
async def fetch_user(http: Http):
    result = await http.get("https://api.example.com/users/1")
    
    print(f"Status: {result.status}")
    print(f"Response: {result.response.text}")
```

### GET con Query Parameters

```python
@inject
async def search_users(http: Http):
    result = await http.get(
        "https://api.example.com/users",
        params={
            "page": 1,
            "limit": 10,
            "search": "john",
            "sort": "name:asc"
        }
    )
    # GET /users?page=1&limit=10&search=john&sort=name:asc
    
    return result
```

### GET con Headers

```python
@inject
async def fetch_protected_resource(http: Http):
    result = await http.get(
        "https://api.example.com/protected",
        headers={
            "Authorization": "Bearer eyJhbGc...",
            "X-API-Key": "secret-key",
            "Accept": "application/json"
        }
    )
    
    return result
```

### GET con Timeout

```python
@inject
async def fetch_with_timeout(http: Http):
    result = await http.get(
        "https://api.example.com/slow-endpoint",
        timeout=5.0  # 5 segundos
    )
    
    if result.exception:
        print("Request timed out")
    
    return result
```

## POST Requests

### POST con JSON

```python
@inject
async def create_user(http: Http):
    result = await http.post(
        "https://api.example.com/users",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30
        }
    )
    
    if result.status == 201:
        print("User created successfully")
    
    return result
```

### POST con Form Data

```python
@inject
async def submit_form(http: Http):
    result = await http.post(
        "https://api.example.com/form",
        data={
            "username": "johndoe",
            "password": "secret123",
            "remember": "true"
        }
    )
    # Content-Type: application/x-www-form-urlencoded
    
    return result
```

### POST con Headers

```python
@inject
async def create_with_auth(http: Http):
    result = await http.post(
        "https://api.example.com/users",
        json={"name": "John"},
        headers={
            "Authorization": "Bearer token123",
            "Content-Type": "application/json"
        }
    )
    
    return result
```

### POST con Bytes

```python
@inject
async def upload_file(http: Http):
    with open("image.jpg", "rb") as f:
        content = f.read()
    
    result = await http.post(
        "https://api.example.com/upload",
        content=content,
        headers={"Content-Type": "image/jpeg"}
    )
    
    return result
```

## PUT Requests

### Actualizar Recurso

```python
@inject
async def update_user(http: Http):
    result = await http.put(
        "https://api.example.com/users/1",
        json={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "age": 31
        }
    )
    
    if result.status == 200:
        print("User updated")
    
    return result
```

## PATCH Requests

### Actualización Parcial

```python
@inject
async def update_email(http: Http):
    result = await http.patch(
        "https://api.example.com/users/1",
        json={
            "email": "newemail@example.com"
        }
    )
    
    return result
```

## DELETE Requests

### Eliminar Recurso

```python
@inject
async def delete_user(http: Http):
    result = await http.delete(
        "https://api.example.com/users/1"
    )
    
    if result.status == 204:
        print("User deleted")
    
    return result
```

### DELETE con Headers

```python
@inject
async def delete_with_auth(http: Http):
    result = await http.delete(
        "https://api.example.com/users/1",
        headers={
            "Authorization": "Bearer token123"
        }
    )
    
    return result
```

## Mapeo a DTOs

### Con Dataclasses

```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str
    username: str

@inject
async def get_user(http: Http):
    result = await http.get("https://jsonplaceholder.typicode.com/users/1")
    
    # Mapea automáticamente JSON a User
    user = result.to(User)
    
    if user:
        print(f"Name: {user.name}")
        print(f"Email: {user.email}")
    
    return user
```

### Con Pydantic

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str
    username: str

@inject
async def get_user(http: Http):
    result = await http.get("https://jsonplaceholder.typicode.com/users/1")
    
    # Pydantic con validación automática
    user = result.to(User)
    
    return user
```

### Con Dict

```python
@inject
async def get_user_dict(http: Http):
    result = await http.get("https://api.example.com/users/1")
    
    # Mapea a dict
    user_dict = result.to(dict)
    
    print(user_dict["name"])
    return user_dict
```

### Con List

```python
@inject
async def get_users_list(http: Http):
    result = await http.get("https://api.example.com/users")
    
    # Mapea a lista
    users = result.to(list)
    
    for user in users:
        print(user["name"])
    
    return users
```

## Manejo de Respuestas

### Verificar Status Code

```python
@inject
async def check_status(http: Http):
    result = await http.get("https://api.example.com/users/1")
    
    if result.status == 200:
        print("Success")
    elif result.status == 404:
        print("Not found")
    elif result.status >= 500:
        print("Server error")
```

### Acceder a Response

```python
@inject
async def access_response(http: Http):
    result = await http.get("https://api.example.com/users/1")
    
    # Objeto httpx.Response completo
    print(result.response.status_code)
    print(result.response.headers)
    print(result.response.text)
    print(result.response.json())
    print(result.response.content)
```

### Verificar Excepciones

```python
@inject
async def check_exception(http: Http):
    result = await http.get("https://invalid-url.com")
    
    if result.exception:
        print(f"Error occurred: {result.exception}")
        print(f"Status: {result.status}")  # 0 si no hubo response
```

## Handlers para una Request

### on_status

```python
@inject
async def with_status_handlers(http: Http):
    result = await http.get(
        "https://api.example.com/users/1",
        on_status={
            200: lambda: print("✅ Success"),
            404: lambda: print("❌ Not found"),
            500: lambda: print("⚠️  Server error")
        }
    )
```

### on_exception

```python
@inject
async def with_exception_handler(http: Http):
    result = await http.get(
        "https://api.example.com/users/1",
        on_exception=lambda e: print(f"Error: {e}")
    )
```

### on_before y on_after

```python
@inject
async def with_before_after(http: Http):
    result = await http.get(
        "https://api.example.com/users/1",
        on_before=lambda req: print(f"→ {req.method} {req.url}"),
        on_after=lambda req, res: print(f"← {res.status_code}")
    )
```

## Requests Concurrentes

### asyncio.gather

```python
import asyncio

@inject
async def fetch_multiple_users(http: Http):
    results = await asyncio.gather(
        http.get("https://api.example.com/users/1"),
        http.get("https://api.example.com/users/2"),
        http.get("https://api.example.com/users/3")
    )
    
    users = [r.to(User) for r in results if r.status == 200]
    return users
```

### asyncio.create_task

```python
@inject
async def concurrent_requests(http: Http):
    task1 = asyncio.create_task(http.get("https://api.example.com/users/1"))
    task2 = asyncio.create_task(http.get("https://api.example.com/posts/1"))
    
    user_result = await task1
    post_result = await task2
    
    return (user_result, post_result)
```

## Configuración por Request

### Follow Redirects

```python
@inject
async def no_redirects(http: Http):
    result = await http.get(
        "https://api.example.com/redirect",
        follow_redirects=False
    )
    
    print(result.status)  # Puede ser 301, 302, etc.
```

### Timeout Personalizado

```python
@inject
async def custom_timeout(http: Http):
    # Timeout corto para requests rápidas
    result = await http.get(
        "https://api.example.com/ping",
        timeout=1.0
    )
    
    # Timeout largo para operaciones pesadas
    result = await http.post(
        "https://api.example.com/process",
        json={"data": "..."},
        timeout=60.0
    )
```

## Ejemplos Prácticos

### API REST Completa

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Todo:
    id: Optional[int]
    title: str
    completed: bool = False

@inject
async def crud_operations(http: Http):
    # CREATE
    create_result = await http.post(
        "https://jsonplaceholder.typicode.com/todos",
        json={"title": "New Todo", "completed": False}
    )
    todo = create_result.to(Todo)
    print(f"Created: {todo.title}")
    
    # READ
    read_result = await http.get(
        "https://jsonplaceholder.typicode.com/todos/1"
    )
    todo = read_result.to(Todo)
    print(f"Read: {todo.title}")
    
    # UPDATE
    update_result = await http.put(
        "https://jsonplaceholder.typicode.com/todos/1",
        json={"title": "Updated Todo", "completed": True}
    )
    todo = update_result.to(Todo)
    print(f"Updated: {todo.title}")
    
    # DELETE
    delete_result = await http.delete(
        "https://jsonplaceholder.typicode.com/todos/1"
    )
    print(f"Deleted: {delete_result.status}")
```

### Autenticación y Headers

```python
@inject
async def authenticated_requests(http: Http):
    # Login
    login_result = await http.post(
        "https://api.example.com/auth/login",
        json={"username": "user", "password": "pass"}
    )
    
    token = login_result.to(dict).get("token")
    
    # Usar token en requests
    profile_result = await http.get(
        "https://api.example.com/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    profile = profile_result.to(dict)
    return profile
```

### Paginación

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

### Rate Limiting Manual

```python
import asyncio

@inject
async def rate_limited_requests(http: Http):
    results = []
    
    for i in range(10):
        result = await http.get(f"https://api.example.com/users/{i}")
        results.append(result)
        
        # Esperar 100ms entre requests
        await asyncio.sleep(0.1)
    
    return results
```

## Errores Comunes

### Timeout

```python
@inject
async def handle_timeout(http: Http):
    result = await http.get(
        "https://slow-api.example.com/data",
        timeout=5.0
    )
    
    if result.exception:
        print("Request timed out or failed")
        return None
    
    return result.to(dict)
```

### JSON Parse Error

```python
@inject
async def handle_json_error(http: Http):
    result = await http.get("https://api.example.com/data")
    
    # .to() retorna None si falla el parsing
    data = result.to(dict)
    
    if data is None:
        print("Failed to parse JSON")
        return {}
    
    return data
```

### Network Error

```python
@inject
async def handle_network_error(http: Http):
    result = await http.get("https://unreachable-api.example.com")
    
    if result.exception:
        print(f"Network error: {result.exception}")
        return None
    
    return result
```

## Próximos Pasos

- [Advanced Features](advanced.md) - Retry, handlers globales, proxy rotation
- [Result Pattern](result.md) - Manejo avanzado de respuestas
- [API Reference](../../api/http.md) - Documentación completa de la API
