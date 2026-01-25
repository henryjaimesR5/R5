# Ejemplos Simples

Ejemplos básicos para empezar rápidamente con R5.

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
    message = service.greet("World")
    print(message)

if __name__ == "__main__":
    asyncio.run(main())
```

**Ejecución:**
```bash
uv run python hello.py
# Output: Hello, World!
```

## HTTP - Fetch API

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
        print(f"✅ User: {user.name}")
        print(f"   Email: {user.email}")

if __name__ == "__main__":
    asyncio.run(fetch_user())
```

**Ejecución:**
```bash
uv run python fetch_user.py
```

## Background - Tareas Simples

```python
import asyncio
from R5.background import Background
from R5.ioc import inject

def process_item(item_id: int):
    print(f"Processing item {item_id}")

@inject
async def main(bg: Background):
    for i in range(5):
        await bg.add(process_item, i)
    
    await asyncio.sleep(1)
    print("All tasks completed")

if __name__ == "__main__":
    asyncio.run(main())
```

**Ejecución:**
```bash
uv run python background_simple.py
```

## Configuration - Archivo JSON

**config.json:**
```json
{
  "app_name": "MyApp",
  "port": 8080,
  "debug": true
}
```

**app.py:**
```python
from R5.ioc import config, inject

@config(file='config.json')
class AppConfig:
    app_name: str = "DefaultApp"
    port: int = 3000
    debug: bool = False

@inject
async def main(config: AppConfig):
    print(f"App: {config.app_name}")
    print(f"Port: {config.port}")
    print(f"Debug: {config.debug}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

**Ejecución:**
```bash
uv run python app.py
```

## Todo List API

```python
import asyncio
from dataclasses import dataclass
from typing import Optional
from R5.http import Http
from R5.ioc import inject

@dataclass
class Todo:
    id: Optional[int]
    title: str
    completed: bool = False
    userId: int = 1

@inject
async def todo_crud(http: Http):
    base_url = "https://jsonplaceholder.typicode.com"
    
    # CREATE
    print("Creating todo...")
    new_todo = Todo(id=None, title="Learn R5", completed=False)
    create_result = await http.post(
        f"{base_url}/todos",
        json={"title": new_todo.title, "completed": new_todo.completed, "userId": 1}
    )
    created = create_result.to(Todo)
    print(f"✅ Created: {created.title} (ID: {created.id})")
    
    # READ
    print("\nReading todo...")
    read_result = await http.get(f"{base_url}/todos/1")
    todo = read_result.to(Todo)
    print(f"✅ Read: {todo.title}")
    
    # UPDATE
    print("\nUpdating todo...")
    update_result = await http.put(
        f"{base_url}/todos/1",
        json={"title": "Master R5", "completed": True, "userId": 1}
    )
    updated = update_result.to(Todo)
    print(f"✅ Updated: {updated.title} (Completed: {updated.completed})")
    
    # DELETE
    print("\nDeleting todo...")
    delete_result = await http.delete(f"{base_url}/todos/1")
    print(f"✅ Deleted (Status: {delete_result.status})")

if __name__ == "__main__":
    asyncio.run(todo_crud())
```

## Email Service

```python
import asyncio
from R5.ioc import singleton, inject
from R5.background import Background

@singleton
class EmailService:
    def send(self, to: str, subject: str, body: str):
        print(f"📧 Sending email to {to}")
        print(f"   Subject: {subject}")
        print(f"   Body: {body}")

@inject
async def send_emails(bg: Background, email: EmailService):
    users = [
        ("user1@example.com", "John"),
        ("user2@example.com", "Jane"),
        ("user3@example.com", "Bob")
    ]
    
    for email_addr, name in users:
        await bg.add(
            email.send,
            email_addr,
            "Welcome!",
            f"Hi {name}, welcome to our platform!"
        )
    
    await asyncio.sleep(1)
    print("\n✅ All emails sent")

if __name__ == "__main__":
    asyncio.run(send_emails())
```

## Logger Service

```python
import asyncio
from datetime import datetime
from R5.ioc import singleton, inject

@singleton
class Logger:
    def info(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[INFO] [{timestamp}] {message}")
    
    def error(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[ERROR] [{timestamp}] {message}")

@singleton
class UserService:
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def create_user(self, username: str):
        self.logger.info(f"Creating user: {username}")
        # Create user logic
        self.logger.info(f"User created: {username}")

@inject
async def main(user_service: UserService):
    user_service.create_user("john_doe")
    user_service.create_user("jane_doe")

if __name__ == "__main__":
    asyncio.run(main())
```

## API Client con Retry

```python
import asyncio
from R5.http import Http
from R5.ioc import inject

@inject
async def fetch_with_retry(http: Http):
    result = await http.retry(
        attempts=3,
        delay=1.0,
        when_status=(500, 502, 503)
    ).get("https://jsonplaceholder.typicode.com/posts/1")
    
    if result.status == 200:
        data = result.to(dict)
        print(f"✅ Title: {data['title']}")
    else:
        print(f"❌ Failed with status: {result.status}")

if __name__ == "__main__":
    asyncio.run(fetch_with_retry())
```

## Cache Service

```python
import asyncio
from typing import Any, Optional
from R5.ioc import singleton, inject

@singleton
class CacheService:
    def __init__(self):
        self._cache: dict[str, Any] = {}
    
    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
    
    def set(self, key: str, value: Any):
        self._cache[key] = value
        print(f"Cached: {key}")
    
    def clear(self):
        self._cache.clear()
        print("Cache cleared")

@inject
async def use_cache(cache: CacheService):
    # Set values
    cache.set("user:1", {"name": "John", "email": "john@example.com"})
    cache.set("user:2", {"name": "Jane", "email": "jane@example.com"})
    
    # Get values
    user1 = cache.get("user:1")
    print(f"Retrieved: {user1}")
    
    # Clear cache
    cache.clear()

if __name__ == "__main__":
    asyncio.run(use_cache())
```

## Parallel HTTP Requests

```python
import asyncio
from R5.http import Http
from R5.ioc import inject

@inject
async def fetch_multiple(http: Http):
    urls = [
        "https://jsonplaceholder.typicode.com/users/1",
        "https://jsonplaceholder.typicode.com/users/2",
        "https://jsonplaceholder.typicode.com/users/3"
    ]
    
    results = await asyncio.gather(*[
        http.get(url) for url in urls
    ])
    
    for i, result in enumerate(results, 1):
        if result.status == 200:
            user = result.to(dict)
            print(f"User {i}: {user['name']}")

if __name__ == "__main__":
    asyncio.run(fetch_multiple())
```

## Environment Variables

**.env:**
```env
DATABASE_URL=postgresql://localhost/mydb
API_KEY=secret-key-123
DEBUG=true
PORT=8080
```

**app.py:**
```python
import asyncio
from R5.ioc import config, inject

@config(file='.env')
class AppConfig:
    database_url: str
    api_key: str
    debug: bool
    port: int

@inject
async def main(config: AppConfig):
    print(f"Database: {config.database_url}")
    print(f"API Key: {config.api_key[:10]}...")
    print(f"Debug: {config.debug}")
    print(f"Port: {config.port}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Factory Pattern

```python
import asyncio
from uuid import uuid4
from R5.ioc import factory, inject, Container

@factory
class RequestContext:
    def __init__(self):
        self.id = uuid4()
        self.timestamp = asyncio.get_event_loop().time()
    
    def __repr__(self):
        return f"Request({self.id})"

@inject
async def main():
    ctx1 = Container.resolve(RequestContext)
    ctx2 = Container.resolve(RequestContext)
    
    print(f"Context 1: {ctx1}")
    print(f"Context 2: {ctx2}")
    print(f"Different instances: {ctx1 is not ctx2}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Ejecución de Todos los Ejemplos

Crea un archivo `run_examples.sh`:

```bash
#!/bin/bash

echo "Running R5 Examples..."
echo "====================="

echo "\n1. Hello World"
uv run python hello.py

echo "\n2. Fetch User"
uv run python fetch_user.py

echo "\n3. Background Tasks"
uv run python background_simple.py

echo "\n4. Configuration"
uv run python app.py

echo "\n5. Todo CRUD"
uv run python todo_crud.py

echo "\n6. Email Service"
uv run python email_service.py

echo "\n7. Logger"
uv run python logger_example.py

echo "\n8. Retry"
uv run python retry_example.py

echo "\n9. Cache"
uv run python cache_example.py

echo "\n10. Parallel Requests"
uv run python parallel_requests.py

echo "\nAll examples completed!"
```

Ejecuta:
```bash
chmod +x run_examples.sh
./run_examples.sh
```
