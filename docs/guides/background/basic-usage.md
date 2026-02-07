# Background Tasks - Uso Básico

## Setup

Background se inyecta automáticamente via IoC:

```python
from R5.background import Background
from R5.ioc import inject
import asyncio

@inject
async def my_service(bg: Background):
    await bg.add(my_task, "arg1")
    await asyncio.sleep(1)  # Esperar a que terminen
```

## Tareas Síncronas

Ejecutan en thread pool automáticamente:

```python
def process_order(order_id: int, user_id: int, amount: float):
    print(f"Processing order {order_id}: ${amount}")
    time.sleep(0.2)

@inject
async def queue_orders(bg: Background):
    await bg.add(process_order, 1, 100, 99.99)
    await bg.add(process_order, 2, 101, 149.99)
    await asyncio.sleep(1)
```

## Tareas Asíncronas

Ejecutan en el event loop:

```python
async def fetch_and_process(url: str):
    await asyncio.sleep(0.1)
    print(f"Processed: {url}")

@inject
async def queue_fetches(bg: Background):
    await bg.add(fetch_and_process, "https://api.example.com/data/1")
    await bg.add(fetch_and_process, "https://api.example.com/data/2")
    await asyncio.sleep(2)
```

Background detecta automáticamente si la tarea es sync o async.

## Batch Processing

```python
@inject
async def batch(bg: Background):
    for i in range(100):
        await bg.add(process_item, i)

    print("100 tasks queued")
    await asyncio.sleep(5)
```

## Manejo de Errores

Los errores en una tarea no detienen las demás:

```python
def failing_task():
    raise Exception("Failed")

def ok_task():
    print("This still runs")

@inject
async def with_errors(bg: Background):
    await bg.add(failing_task)   # Falla, se loguea como WARNING
    await bg.add(ok_task)        # Se ejecuta normalmente
    await asyncio.sleep(0.5)
```

### Retry dentro de la tarea

```python
def task_with_retry(item_id: int, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            process_item(item_id)
            break
        except Exception:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
```

## Lifecycle

```python
# Automático via @inject
@inject
async def auto(bg: Background):
    await bg.add(task1)
    await asyncio.sleep(1)

# Manual via context manager
async def manual():
    bg = Container.resolve(Background)
    async with bg:
        await bg.add(task1)
        await asyncio.sleep(1)
    # Cleanup automático
```

## Ejemplo: Envío de Emails

```python
def send_email(to: str, subject: str, body: str):
    print(f"Sending to {to}: {subject}")
    time.sleep(0.2)

@inject
async def send_welcome_emails(bg: Background):
    users = [("user1@example.com", "John"), ("user2@example.com", "Jane")]

    for email, name in users:
        await bg.add(send_email, email, "Welcome!", f"Hi {name}!")

    await asyncio.sleep(1)
```

## Próximos Pasos

- [IoC Integration](ioc-integration.md) - Inyección de dependencias en tareas
- [Overview](overview.md) - Arquitectura y características
