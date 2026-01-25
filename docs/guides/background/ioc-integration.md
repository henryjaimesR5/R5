# Background Tasks - Integración con IoC

Las tareas en Background pueden recibir dependencias inyectadas automáticamente.

## Inyección Automática

Background detecta y resuelve dependencias automáticamente:

```python
from R5.ioc import singleton, inject
from R5.background import Background

@singleton
class EmailService:
    def send(self, to: str, subject: str):
        print(f"Sending email to {to}: {subject}")

def send_welcome_email(email_service: EmailService, user_email: str):
    # EmailService se inyecta automáticamente
    email_service.send(user_email, "Welcome!")

@inject
async def queue_emails(bg: Background):
    await bg.add(send_welcome_email, user_email="user@example.com")
    await asyncio.sleep(0.5)
```

## Tareas con Múltiples Dependencias

```python
@singleton
class Logger:
    def log(self, msg: str):
        print(f"[LOG] {msg}")

@singleton
class Database:
    def save(self, data: str):
        print(f"Saving to DB: {data}")

def process_order(
    logger: Logger,
    db: Database,
    order_id: int
):
    logger.log(f"Processing order {order_id}")
    db.save(f"order_{order_id}")
    logger.log(f"Order {order_id} processed")

@inject
async def queue_order_processing(bg: Background):
    # Logger y Database se inyectan automáticamente
    await bg.add(process_order, order_id=123)
    await asyncio.sleep(1)
```

## Async Tasks con IoC

```python
@singleton
class HttpClient:
    async def fetch(self, url: str):
        print(f"Fetching {url}")
        return {"data": "example"}

async def fetch_and_log(
    client: HttpClient,
    logger: Logger,
    url: str
):
    logger.log(f"Fetching {url}")
    data = await client.fetch(url)
    logger.log(f"Fetched: {data}")

@inject
async def queue_fetches(bg: Background):
    await bg.add(fetch_and_log, url="https://api.example.com/data")
    await asyncio.sleep(2)
```

## Mezclando Dependencias y Parámetros

```python
@singleton
class ConfigService:
    def get(self, key: str) -> str:
        return f"config_{key}"

def process_with_config(
    config: ConfigService,  # Inyectado
    item_id: int,           # Parámetro manual
    priority: str = "normal"  # Parámetro con default
):
    api_key = config.get("api_key")
    print(f"Processing item {item_id} with priority {priority}")
    print(f"Using API key: {api_key}")

@inject
async def queue_processing(bg: Background):
    # Solo pasamos los parámetros no inyectables
    await bg.add(process_with_config, item_id=42, priority="high")
    await bg.add(process_with_config, item_id=43)  # Usa default priority
    
    await asyncio.sleep(1)
```

## Service Layer Pattern

```python
@singleton
class UserRepository:
    def find(self, user_id: int):
        return {"id": user_id, "name": "John"}

@singleton
class EmailService:
    def send(self, to: str, message: str):
        print(f"Email to {to}: {message}")

@singleton
class UserService:
    def __init__(self, repo: UserRepository, email: EmailService):
        self.repo = repo
        self.email = email
    
    def notify_user(self, user_id: int, message: str):
        user = self.repo.find(user_id)
        self.email.send(user["email"], message)

def background_notification(
    user_service: UserService,  # Inyectado con sus dependencias
    user_id: int,
    message: str
):
    user_service.notify_user(user_id, message)

@inject
async def queue_notifications(bg: Background):
    await bg.add(background_notification, user_id=1, message="Hello!")
    await bg.add(background_notification, user_id=2, message="Welcome!")
    
    await asyncio.sleep(1)
```

## Scopes en Background

### Singleton

Tareas comparten la misma instancia:

```python
@singleton
class Counter:
    def __init__(self):
        self.count = 0
    
    def increment(self):
        self.count += 1
        print(f"Count: {self.count}")

def increment_counter(counter: Counter):
    counter.increment()

@inject
async def test_singleton(bg: Background):
    for i in range(5):
        await bg.add(increment_counter)
    
    await asyncio.sleep(1)
    # Output: Count: 1, Count: 2, Count: 3, Count: 4, Count: 5
    # Todas las tareas usan la misma instancia
```

### Factory

Cada tarea recibe una nueva instancia:

```python
@factory
class RequestContext:
    def __init__(self):
        self.id = uuid4()
        print(f"Created context {self.id}")

def process_with_context(ctx: RequestContext, item_id: int):
    print(f"Processing {item_id} with context {ctx.id}")

@inject
async def test_factory(bg: Background):
    for i in range(3):
        await bg.add(process_with_context, item_id=i)
    
    await asyncio.sleep(1)
    # Cada tarea recibe un nuevo RequestContext
```

## Configuration en Background

```python
@config(file='.env')
class AppConfig:
    api_key: str = ""
    max_retries: int = 3

def api_call_with_config(
    config: AppConfig,
    endpoint: str
):
    print(f"Calling {endpoint} with key {config.api_key}")
    print(f"Max retries: {config.max_retries}")

@inject
async def queue_api_calls(bg: Background):
    await bg.add(api_call_with_config, endpoint="/users")
    await bg.add(api_call_with_config, endpoint="/posts")
    
    await asyncio.sleep(1)
```

## Http Client en Background

```python
from R5.http import Http

async def fetch_and_process(
    http: Http,  # Inyectado
    logger: Logger,  # Inyectado
    url: str  # Parámetro
):
    logger.log(f"Fetching {url}")
    result = await http.get(url)
    
    if result.status == 200:
        data = result.to(dict)
        logger.log(f"Success: {data}")
    else:
        logger.log(f"Failed: {result.status}")

@inject
async def queue_http_tasks(bg: Background):
    urls = [
        "https://api.example.com/users/1",
        "https://api.example.com/users/2",
        "https://api.example.com/users/3"
    ]
    
    for url in urls:
        await bg.add(fetch_and_process, url=url)
    
    await asyncio.sleep(3)
```

## Nested Background en Background

```python
@inject
async def nested_task(bg: Background, item_id: int):
    # Una tarea puede encolar más tareas
    await bg.add(lambda: print(f"Sub-task for item {item_id}"))

@inject
async def parent_task(bg: Background):
    for i in range(3):
        await bg.add(nested_task, item_id=i)
    
    await asyncio.sleep(2)
```

## Caché de Dependencias

Background cachea las dependencias resueltas para mejor rendimiento:

```python
@singleton
class HeavyService:
    def __init__(self):
        print("Initializing HeavyService (expensive)")
        time.sleep(1)
    
    def process(self, item: int):
        print(f"Processing {item}")

def task_with_heavy_service(service: HeavyService, item: int):
    service.process(item)

@inject
async def test_cache(bg: Background):
    # HeavyService se crea solo una vez
    for i in range(10):
        await bg.add(task_with_heavy_service, item=i)
    
    await asyncio.sleep(3)
    # Output: "Initializing HeavyService" solo una vez
```

## Ejemplo Completo: Worker Queue

```python
@config(file='.env')
class WorkerConfig:
    worker_count: int = 4
    retry_attempts: int = 3

@singleton
class JobRepository:
    def get_pending_jobs(self):
        return [
            {"id": 1, "type": "email", "data": "user1@example.com"},
            {"id": 2, "type": "sms", "data": "+1234567890"},
            {"id": 3, "type": "push", "data": "device_token_123"}
        ]
    
    def mark_completed(self, job_id: int):
        print(f"Job {job_id} marked as completed")

@singleton
class NotificationService:
    def send_email(self, email: str):
        print(f"Sending email to {email}")
    
    def send_sms(self, phone: str):
        print(f"Sending SMS to {phone}")
    
    def send_push(self, token: str):
        print(f"Sending push to {token}")

def process_job(
    repo: JobRepository,
    notifications: NotificationService,
    logger: Logger,
    job: dict
):
    logger.log(f"Processing job {job['id']}")
    
    try:
        if job["type"] == "email":
            notifications.send_email(job["data"])
        elif job["type"] == "sms":
            notifications.send_sms(job["data"])
        elif job["type"] == "push":
            notifications.send_push(job["data"])
        
        repo.mark_completed(job["id"])
        logger.log(f"Job {job['id']} completed")
    except Exception as e:
        logger.log(f"Job {job['id']} failed: {e}")

@inject
async def worker_queue(
    bg: Background,
    repo: JobRepository,
    logger: Logger
):
    logger.log("Starting worker queue")
    
    jobs = repo.get_pending_jobs()
    
    for job in jobs:
        await bg.add(process_job, job=job)
    
    logger.log(f"Queued {len(jobs)} jobs")
    await asyncio.sleep(2)
    logger.log("Worker queue finished")

if __name__ == "__main__":
    asyncio.run(worker_queue())
```

## Testing con IoC

```python
def test_background_with_mocks():
    Container.reset()
    
    # Mock services
    @singleton
    class MockLogger:
        def __init__(self):
            self.logs = []
        
        def log(self, msg: str):
            self.logs.append(msg)
    
    def task_with_logger(logger: MockLogger, message: str):
        logger.log(message)
    
    async def test():
        bg = Container.resolve(Background)
        logger = Container.resolve(MockLogger)
        
        async with bg:
            await bg.add(task_with_logger, message="test1")
            await bg.add(task_with_logger, message="test2")
            await asyncio.sleep(0.5)
        
        assert "test1" in logger.logs
        assert "test2" in logger.logs
    
    asyncio.run(test())
```

## Patrones Avanzados

### Event-Driven Architecture

```python
@singleton
class EventBus:
    def __init__(self):
        self.handlers = {}
    
    def subscribe(self, event_type: str, handler):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    async def publish(self, bg: Background, event_type: str, data: dict):
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                await bg.add(handler, data=data)

def on_user_registered(logger: Logger, data: dict):
    logger.log(f"User registered: {data['email']}")

def on_user_registered_send_email(email_service: EmailService, data: dict):
    email_service.send(data["email"], "Welcome!")

@inject
async def setup_events(event_bus: EventBus):
    event_bus.subscribe("user.registered", on_user_registered)
    event_bus.subscribe("user.registered", on_user_registered_send_email)

@inject
async def trigger_event(bg: Background, event_bus: EventBus):
    await event_bus.publish(
        bg,
        "user.registered",
        {"email": "user@example.com"}
    )
    
    await asyncio.sleep(1)
```

### Command Pattern

```python
@singleton
class CommandExecutor:
    async def execute(self, bg: Background, command):
        await bg.add(command.execute)

class SendEmailCommand:
    def __init__(self, to: str, subject: str):
        self.to = to
        self.subject = subject
    
    def execute(self, email_service: EmailService):
        email_service.send(self.to, self.subject)

@inject
async def execute_commands(bg: Background, executor: CommandExecutor):
    cmd1 = SendEmailCommand("user1@example.com", "Hello")
    cmd2 = SendEmailCommand("user2@example.com", "Welcome")
    
    await executor.execute(bg, cmd1)
    await executor.execute(bg, cmd2)
    
    await asyncio.sleep(1)
```

## Próximos Pasos

- [Overview](overview.md) - Visión general de Background
- [Basic Usage](basic-usage.md) - Uso básico
- [API Reference](../../api/background.md) - Documentación completa
