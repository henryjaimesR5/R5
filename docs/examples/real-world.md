# Ejemplos del Mundo Real

Aplicaciones completas usando R5.

## API REST con Autenticación

```python
# config.py
from R5.ioc import config

@config(file='.env')
class AppConfig:
    database_url: str = "sqlite:///app.db"
    secret_key: str = "dev-secret"
    jwt_algorithm: str = "HS256"
    token_expire_minutes: int = 30

# services.py
from R5.ioc import singleton
import jwt
from datetime import datetime, timedelta

@singleton
class Logger:
    def info(self, msg: str): print(f"[INFO] {msg}")
    def error(self, msg: str): print(f"[ERROR] {msg}")

@singleton
class AuthService:
    def __init__(self, config: AppConfig):
        self.config = config

    def create_token(self, user_id: int) -> str:
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(minutes=self.config.token_expire_minutes)
        }
        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.jwt_algorithm)

    def verify_token(self, token: str) -> dict:
        return jwt.decode(token, self.config.secret_key, algorithms=[self.config.jwt_algorithm])

@singleton
class DatabaseService:
    def __init__(self, config: AppConfig, logger: Logger):
        self.url = config.database_url
        self.logger = logger

    def connect(self):
        self.logger.info(f"Connected to {self.url}")

# main.py
@inject
async def main(db: DatabaseService, auth: AuthService, logger: Logger):
    db.connect()
    token = auth.create_token(user_id=123)
    payload = auth.verify_token(token)
    logger.info(f"Verified user: {payload['user_id']}")
```

## Web Scraper Concurrente

```python
from R5.http import Http
from R5.ioc import singleton, inject, config
from R5.background import Background

@config(file='.env')
class ScraperConfig:
    max_concurrent: int = 5
    request_delay: float = 1.0

@singleton
class RateLimiter:
    def __init__(self, config: ScraperConfig):
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        self.delay = config.request_delay

    async def acquire(self):
        await self.semaphore.acquire()
        await asyncio.sleep(self.delay)

    def release(self):
        self.semaphore.release()

@singleton
class Scraper:
    def __init__(self, http: Http, limiter: RateLimiter):
        self.http = http
        self.limiter = limiter

    async def scrape(self, url: str) -> dict | None:
        await self.limiter.acquire()
        try:
            result = await self.http.retry(attempts=3, delay=1.0).get(url)
            if result.status == 200:
                return {"url": url, "status": 200, "size": len(result.response.text)}
            return None
        finally:
            self.limiter.release()

@inject
async def main(scraper: Scraper):
    urls = ["https://example.com", "https://example.org", "https://example.net"]
    results = await asyncio.gather(*[scraper.scrape(url) for url in urls])
    for r in results:
        if r:
            print(f"{r['url']}: {r['size']} bytes")
```

## Sistema de Notificaciones Multi-Canal

```python
from abc import ABC, abstractmethod
from enum import Enum

class Channel(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class NotificationProvider(ABC):
    @abstractmethod
    async def send(self, recipient: str, message: str): ...

@singleton
class EmailProvider(NotificationProvider):
    async def send(self, recipient: str, message: str):
        print(f"Email to {recipient}: {message}")

@singleton
class SMSProvider(NotificationProvider):
    async def send(self, recipient: str, message: str):
        print(f"SMS to {recipient}: {message}")

@singleton
class PushProvider(NotificationProvider):
    async def send(self, recipient: str, message: str):
        print(f"Push to {recipient}: {message}")

@singleton
class NotificationService:
    def __init__(self, email: EmailProvider, sms: SMSProvider, push: PushProvider):
        self.providers = {
            Channel.EMAIL: email,
            Channel.SMS: sms,
            Channel.PUSH: push,
        }

    async def send(self, channel: Channel, recipient: str, message: str):
        provider = self.providers.get(channel)
        if provider:
            await provider.send(recipient, message)

@inject
async def main(bg: Background, notif: NotificationService):
    notifications = [
        (Channel.EMAIL, "user@example.com", "Welcome!"),
        (Channel.SMS, "+1234567890", "Code: 123456"),
        (Channel.PUSH, "device_token", "New message"),
    ]
    for channel, recipient, msg in notifications:
        await bg.add(notif.send, channel, recipient, msg)
    await asyncio.sleep(2)
```

## Task Queue con Prioridades

```python
from enum import Enum
from dataclasses import dataclass

class Priority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class Job:
    id: int
    name: str
    handler: Callable
    args: tuple
    priority: Priority

@singleton
class TaskQueue:
    def __init__(self):
        self.jobs: list[Job] = []
        self.completed: set[int] = set()

    def add(self, name: str, handler: Callable, priority: Priority = Priority.NORMAL, *args):
        job = Job(len(self.jobs) + 1, name, handler, args, priority)
        self.jobs.append(job)

    def next(self) -> Job | None:
        pending = [j for j in self.jobs if j.id not in self.completed]
        if not pending:
            return None
        pending.sort(key=lambda j: j.priority.value, reverse=True)
        return pending[0]

    def done(self, job_id: int):
        self.completed.add(job_id)

@inject
async def main(bg: Background, queue: TaskQueue):
    queue.add("alert", send_alert, Priority.CRITICAL, "System down")
    queue.add("email", send_email, Priority.HIGH, "user@example.com")
    queue.add("cleanup", cleanup, Priority.LOW)

    while job := queue.next():
        await bg.add(lambda j=job: (j.handler(*j.args), queue.done(j.id)))

    await asyncio.sleep(2)
```

## Próximos Pasos

- [Ejemplos simples](simple.md) - Ejemplos básicos
- [Patrones](patterns.md) - Patrones de diseño
