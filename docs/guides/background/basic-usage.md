# Background Tasks - Uso Básico

Guía práctica para ejecutar tareas en background con R5.

## Setup Inicial

```python
from R5.background import Background
from R5.ioc import inject
import asyncio

@inject
async def my_service(bg: Background):
    await bg.add(my_task, "arg1", "arg2")
    await asyncio.sleep(1)  # Esperar a que terminen
```

Background se inyecta automáticamente, no necesitas crear instancias manualmente.

## Tareas Síncronas

### Función Simple

```python
def send_email(to: str):
    print(f"Sending email to {to}")
    time.sleep(0.1)
    print("Email sent")

@inject
async def queue_email(bg: Background):
    await bg.add(send_email, "user@example.com")
    await asyncio.sleep(0.5)
```

### Con Múltiples Argumentos

```python
def process_order(order_id: int, user_id: int, amount: float):
    print(f"Processing order {order_id} for user {user_id}: ${amount}")
    time.sleep(0.2)
    print(f"Order {order_id} processed")

@inject
async def queue_orders(bg: Background):
    await bg.add(process_order, 1, 100, 99.99)
    await bg.add(process_order, 2, 101, 149.99)
    
    await asyncio.sleep(1)
```

### Con Keyword Arguments

```python
def create_user(username: str, email: str, age: int = 18):
    print(f"Creating user: {username} ({email}), age {age}")

@inject
async def queue_user_creation(bg: Background):
    await bg.add(create_user, "john", "john@example.com", age=25)
    await bg.add(create_user, username="jane", email="jane@example.com")
    
    await asyncio.sleep(0.5)
```

## Tareas Asíncronas

### Async Function

```python
async def async_task(item_id: int):
    await asyncio.sleep(0.1)
    print(f"Processed item {item_id}")

@inject
async def queue_async_tasks(bg: Background):
    await bg.add(async_task, 1)
    await bg.add(async_task, 2)
    await bg.add(async_task, 3)
    
    await asyncio.sleep(0.5)
```

### Async con HTTP

```python
from R5.http import Http

async def fetch_and_process(http: Http, url: str):
    result = await http.get(url)
    data = result.to(dict)
    print(f"Fetched: {data}")

@inject
async def queue_fetches(bg: Background):
    await bg.add(fetch_and_process, "https://api.example.com/data/1")
    await bg.add(fetch_and_process, "https://api.example.com/data/2")
    
    await asyncio.sleep(2)
```

### Async con Await

```python
async def download_file(url: str, filename: str):
    print(f"Downloading {url}...")
    await asyncio.sleep(0.5)  # Simula descarga
    print(f"Saved to {filename}")

@inject
async def queue_downloads(bg: Background):
    await bg.add(download_file, "https://example.com/file1.pdf", "file1.pdf")
    await bg.add(download_file, "https://example.com/file2.pdf", "file2.pdf")
    
    await asyncio.sleep(2)
```

## Lambdas

### Lambda Simple

```python
@inject
async def with_lambda(bg: Background):
    await bg.add(lambda: print("Hello from lambda"))
    await bg.add(lambda x: print(f"Lambda with arg: {x}"), 42)
    
    await asyncio.sleep(0.5)
```

### Lambda Capturando Variables

```python
@inject
async def with_captured_lambda(bg: Background):
    user_id = 123
    message = "Welcome!"
    
    await bg.add(
        lambda: print(f"Sending {message} to user {user_id}")
    )
    
    await asyncio.sleep(0.5)
```

## Bucles

### For Loop

```python
@inject
async def queue_many(bg: Background):
    for i in range(10):
        await bg.add(process_item, i)
    
    print("10 tasks queued")
    await asyncio.sleep(1)
```

### List Comprehension

```python
@inject
async def queue_from_list(bg: Background):
    items = [1, 2, 3, 4, 5]
    
    for item in items:
        await bg.add(process_item, item)
    
    await asyncio.sleep(1)
```

### Batch Processing

```python
@inject
async def batch_process(bg: Background):
    batch = range(100)
    
    for item_id in batch:
        await bg.add(process_item, item_id)
    
    print(f"Queued {len(batch)} items")
    await asyncio.sleep(5)
```

## Diferentes Tipos de Tareas

### Mezclando Sync y Async

```python
def sync_task(data: str):
    print(f"Sync: {data}")

async def async_task(data: str):
    print(f"Async: {data}")

@inject
async def mixed_tasks(bg: Background):
    await bg.add(sync_task, "task1")   # Thread pool
    await bg.add(async_task, "task2")  # Event loop
    await bg.add(sync_task, "task3")   # Thread pool
    await bg.add(async_task, "task4")  # Event loop
    
    await asyncio.sleep(0.5)
```

### Tareas con Duraciones Diferentes

```python
def quick_task():
    time.sleep(0.1)
    print("Quick task done")

def slow_task():
    time.sleep(1.0)
    print("Slow task done")

@inject
async def mixed_duration(bg: Background):
    await bg.add(quick_task)
    await bg.add(slow_task)
    await bg.add(quick_task)
    
    await asyncio.sleep(2)
    # quick_task termina primero, slow_task después
```

## Esperar Tareas

### Sleep Explícito

```python
@inject
async def wait_for_tasks(bg: Background):
    await bg.add(task1)
    await bg.add(task2)
    
    # Esperar a que terminen
    await asyncio.sleep(2)
    
    print("All tasks completed")
```

### Esperar Tiempo Estimado

```python
@inject
async def wait_estimated(bg: Background):
    task_count = 100
    task_duration = 0.1
    
    for i in range(task_count):
        await bg.add(process_item, i)
    
    # Esperar tiempo estimado
    await asyncio.sleep(task_duration * 2)
```

## Manejo de Errores

### Tarea que Falla

```python
def failing_task():
    raise Exception("This task fails")

def successful_task():
    print("This task succeeds")

@inject
async def with_failing_task(bg: Background):
    await bg.add(failing_task)
    await bg.add(successful_task)
    
    await asyncio.sleep(0.5)
    # successful_task se ejecuta aunque failing_task falle
```

### Múltiples Fallos

```python
@inject
async def multiple_failures(bg: Background):
    for i in range(5):
        if i % 2 == 0:
            await bg.add(lambda: print(f"Task {i} success"))
        else:
            await bg.add(lambda: 1/0)  # Falla
    
    await asyncio.sleep(1)
    # Tareas exitosas se ejecutan normalmente
```

## Ejemplos Prácticos

### Envío de Emails

```python
def send_email(to: str, subject: str, body: str):
    print(f"Sending email to {to}")
    time.sleep(0.2)
    print(f"Email sent: {subject}")

@inject
async def send_welcome_emails(bg: Background):
    users = [
        ("user1@example.com", "John"),
        ("user2@example.com", "Jane"),
        ("user3@example.com", "Bob")
    ]
    
    for email, name in users:
        await bg.add(
            send_email,
            email,
            "Welcome!",
            f"Hi {name}, welcome to our platform!"
        )
    
    print("All emails queued")
    await asyncio.sleep(1)
```

### Procesamiento de Pagos

```python
async def process_payment(payment_id: int, amount: float):
    print(f"Processing payment {payment_id}: ${amount}")
    await asyncio.sleep(0.5)
    print(f"Payment {payment_id} completed")

@inject
async def process_pending_payments(bg: Background):
    payments = [
        (1, 99.99),
        (2, 149.99),
        (3, 49.99),
        (4, 199.99)
    ]
    
    for payment_id, amount in payments:
        await bg.add(process_payment, payment_id, amount)
    
    await asyncio.sleep(3)
```

### Actualización de Caché

```python
def update_cache(key: str, value: str):
    print(f"Updating cache: {key} = {value}")
    time.sleep(0.1)
    print(f"Cache updated: {key}")

@inject
async def refresh_cache(bg: Background):
    cache_items = {
        "user:123": "John Doe",
        "user:456": "Jane Smith",
        "config:app": "production",
        "stats:today": "1234"
    }
    
    for key, value in cache_items.items():
        await bg.add(update_cache, key, value)
    
    await asyncio.sleep(1)
```

### Notificaciones Push

```python
async def send_push_notification(user_id: int, message: str):
    print(f"Sending push to user {user_id}: {message}")
    await asyncio.sleep(0.2)
    print(f"Push sent to user {user_id}")

@inject
async def notify_users(bg: Background):
    notifications = [
        (100, "New message"),
        (101, "Friend request"),
        (102, "Post liked"),
        (103, "Comment on your post")
    ]
    
    for user_id, message in notifications:
        await bg.add(send_push_notification, user_id, message)
    
    await asyncio.sleep(2)
```

### Generación de Reportes

```python
def generate_report(report_type: str, user_id: int):
    print(f"Generating {report_type} report for user {user_id}")
    time.sleep(1.0)  # Simulación de proceso pesado
    print(f"Report {report_type} generated for user {user_id}")

@inject
async def queue_reports(bg: Background):
    reports = [
        ("sales", 1),
        ("inventory", 2),
        ("analytics", 3)
    ]
    
    for report_type, user_id in reports:
        await bg.add(generate_report, report_type, user_id)
    
    print("Reports queued")
    await asyncio.sleep(5)
```

### Web Scraping

```python
from R5.http import Http

async def scrape_page(http: Http, url: str):
    print(f"Scraping {url}")
    result = await http.get(url)
    print(f"Scraped {url}: {result.status}")

@inject
async def scrape_multiple_pages(bg: Background):
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3"
    ]
    
    for url in urls:
        await bg.add(scrape_page, url)
    
    await asyncio.sleep(3)
```

## Patrones Avanzados

### Task Priority (Manual)

```python
@inject
async def prioritized_tasks(bg: Background):
    # Alta prioridad primero
    await bg.add(critical_task)
    await bg.add(critical_task)
    
    # Media prioridad
    await bg.add(normal_task)
    await bg.add(normal_task)
    
    # Baja prioridad
    await bg.add(low_priority_task)
    
    await asyncio.sleep(2)
```

### Conditional Queueing

```python
@inject
async def conditional_queue(bg: Background):
    items = range(10)
    
    for item in items:
        if item % 2 == 0:
            await bg.add(even_task, item)
        else:
            await bg.add(odd_task, item)
    
    await asyncio.sleep(1)
```

### Retry Logic in Task

```python
def task_with_retry(item_id: int, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            process_item(item_id)
            break
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Failed after {max_retries} attempts: {e}")
            else:
                time.sleep(2 ** attempt)

@inject
async def queue_with_retry(bg: Background):
    await bg.add(task_with_retry, 1)
    await asyncio.sleep(5)
```

## Limitaciones

### No Retorna Valores

```python
# ❌ No funciona
result = await bg.add(compute_value)

# ✅ Usa callback o side effects
def compute_and_store(results: list):
    value = compute_value()
    results.append(value)

results = []
await bg.add(compute_and_store, results)
await asyncio.sleep(1)
print(results[0])
```

### No Garantiza Orden

```python
@inject
async def unordered(bg: Background):
    await bg.add(task, 1)
    await bg.add(task, 2)
    await bg.add(task, 3)
    
    # Pueden ejecutarse en cualquier orden
    # Si necesitas orden, usa await directamente
```

## Próximos Pasos

- [Overview](overview.md) - Visión general de Background
- [IoC Integration](ioc-integration.md) - Integración con IoC
- [API Reference](../../api/background.md) - Documentación completa
