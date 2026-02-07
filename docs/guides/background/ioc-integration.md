# Background Tasks - Integración con IoC

Las tareas en Background reciben dependencias inyectadas automáticamente.

## Inyección Automática

Background detecta type hints registrados en el container y los resuelve:

```python
@singleton
class EmailService:
    def send(self, to: str, subject: str):
        print(f"Email to {to}: {subject}")

def send_welcome(email_service: EmailService, user_email: str):
    email_service.send(user_email, "Welcome!")

@inject
async def main(bg: Background):
    # EmailService se inyecta, user_email se pasa manualmente
    await bg.add(send_welcome, user_email="user@example.com")
    await asyncio.sleep(0.5)
```

## Múltiples Dependencias

```python
def process_order(logger: Logger, db: Database, order_id: int):
    logger.log(f"Processing order {order_id}")
    db.save(f"order_{order_id}")

@inject
async def queue(bg: Background):
    await bg.add(process_order, order_id=123)  # Logger y DB se inyectan
```

## Async Tasks con IoC

```python
async def fetch_and_log(http: Http, logger: Logger, url: str):
    logger.log(f"Fetching {url}")
    result = await http.get(url)
    logger.log(f"Status: {result.status}")

@inject
async def queue_fetches(bg: Background):
    await bg.add(fetch_and_log, url="https://api.example.com/data")
    await asyncio.sleep(2)
```

## Scopes en Background

### Singleton - Instancia compartida entre tareas

```python
@singleton
class Counter:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1

def task(counter: Counter):
    counter.increment()
    print(f"Count: {counter.count}")

# Todas las tareas usan el mismo Counter
```

### Factory - Nueva instancia por tarea

```python
@factory
class RequestContext:
    def __init__(self):
        self.id = uuid4()

def task(ctx: RequestContext, item_id: int):
    print(f"Item {item_id} with context {ctx.id}")

# Cada tarea recibe un RequestContext diferente
```

### Config en tareas

```python
@config(file='.env')
class AppConfig:
    api_key: str = ""

def api_call(config: AppConfig, endpoint: str):
    print(f"Calling {endpoint} with key {config.api_key}")
```

## Ejemplo: Worker Queue

```python
@singleton
class JobRepository:
    def get_pending(self):
        return [
            {"id": 1, "type": "email", "data": "user@example.com"},
            {"id": 2, "type": "sms", "data": "+1234567890"},
        ]

    def mark_done(self, job_id: int):
        print(f"Job {job_id} done")

@singleton
class NotificationService:
    def send_email(self, email: str): print(f"Email to {email}")
    def send_sms(self, phone: str): print(f"SMS to {phone}")

def process_job(repo: JobRepository, notif: NotificationService, job: dict):
    if job["type"] == "email":
        notif.send_email(job["data"])
    elif job["type"] == "sms":
        notif.send_sms(job["data"])
    repo.mark_done(job["id"])

@inject
async def worker(bg: Background, repo: JobRepository):
    for job in repo.get_pending():
        await bg.add(process_job, job=job)
    await asyncio.sleep(2)
```

## Testing

```python
def test_background_with_mocks():
    Container.reset()

    @singleton
    class MockLogger:
        def __init__(self):
            self.logs = []
        def log(self, msg: str):
            self.logs.append(msg)

    def task(logger: MockLogger, message: str):
        logger.log(message)

    async def run():
        bg = Container.resolve(Background)
        logger = Container.resolve(MockLogger)
        async with bg:
            await bg.add(task, message="test")
            await asyncio.sleep(0.5)
        assert "test" in logger.logs

    asyncio.run(run())
```

## Próximos Pasos

- [Basic Usage](basic-usage.md) - Tareas sync, async, errores
- [Overview](overview.md) - Arquitectura
