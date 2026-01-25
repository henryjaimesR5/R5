# Ejemplos del Mundo Real

Ejemplos completos de aplicaciones reales usando R5.

## API REST Completa

Una API REST con autenticación, base de datos y logging.

**config.py:**
```python
from R5.ioc import config

@config(file='.env')
class AppConfig:
    database_url: str = "sqlite:///app.db"
    secret_key: str = "dev-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    host: str = "0.0.0.0"
    port: int = 8000
```

**services/logger.py:**
```python
from datetime import datetime
from R5.ioc import singleton

@singleton
class Logger:
    def info(self, message: str):
        print(f"[INFO] [{datetime.now()}] {message}")
    
    def error(self, message: str):
        print(f"[ERROR] [{datetime.now()}] {message}")
```

**services/database.py:**
```python
from R5.ioc import singleton

@singleton
class DatabaseService:
    def __init__(self, config: AppConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.connection = None
    
    def connect(self):
        self.logger.info(f"Connecting to {self.config.database_url}")
        # Connection logic
    
    def query(self, sql: str):
        self.logger.info(f"Executing query: {sql}")
        # Query logic
```

**services/auth.py:**
```python
from R5.ioc import singleton
import jwt
from datetime import datetime, timedelta

@singleton
class AuthService:
    def __init__(self, config: AppConfig):
        self.config = config
    
    def create_token(self, user_id: int) -> str:
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(
                minutes=self.config.access_token_expire_minutes
            )
        }
        return jwt.encode(
            payload,
            self.config.secret_key,
            algorithm=self.config.jwt_algorithm
        )
    
    def verify_token(self, token: str) -> dict:
        return jwt.decode(
            token,
            self.config.secret_key,
            algorithms=[self.config.jwt_algorithm]
        )
```

**main.py:**
```python
import asyncio
from R5.ioc import inject

@inject
async def main(
    config: AppConfig,
    db: DatabaseService,
    auth: AuthService,
    logger: Logger
):
    logger.info("Starting application")
    db.connect()
    
    # Simulate login
    token = auth.create_token(user_id=123)
    logger.info(f"Token created: {token[:20]}...")
    
    # Verify token
    payload = auth.verify_token(token)
    logger.info(f"Token verified for user: {payload['user_id']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Web Scraper

Scraper concurrente con rate limiting y caché.

```python
import asyncio
from dataclasses import dataclass
from typing import Optional
from R5.http import Http
from R5.background import Background
from R5.ioc import singleton, inject, config

@config(file='.env')
class ScraperConfig:
    max_concurrent: int = 5
    request_delay: float = 1.0
    retry_attempts: int = 3

@singleton
class CacheService:
    def __init__(self):
        self._cache = {}
    
    def get(self, url: str) -> Optional[str]:
        return self._cache.get(url)
    
    def set(self, url: str, content: str):
        self._cache[url] = content

@singleton
class RateLimiter:
    def __init__(self, config: ScraperConfig):
        self.delay = config.request_delay
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
    
    async def acquire(self):
        await self.semaphore.acquire()
        await asyncio.sleep(self.delay)
    
    def release(self):
        self.semaphore.release()

@dataclass
class ScrapedData:
    url: str
    title: str
    status: int

@singleton
class Scraper:
    def __init__(
        self,
        http: Http,
        cache: CacheService,
        limiter: RateLimiter,
        logger: Logger
    ):
        self.http = http
        self.cache = cache
        self.limiter = limiter
        self.logger = logger
    
    async def scrape(self, url: str) -> Optional[ScrapedData]:
        # Check cache
        cached = self.cache.get(url)
        if cached:
            self.logger.info(f"Cache hit: {url}")
            return cached
        
        # Rate limit
        await self.limiter.acquire()
        
        try:
            self.logger.info(f"Scraping: {url}")
            result = await self.http.get(url)
            
            if result.status == 200:
                data = ScrapedData(
                    url=url,
                    title=result.response.text[:100],
                    status=result.status
                )
                self.cache.set(url, data)
                return data
            else:
                self.logger.error(f"Failed: {url} ({result.status})")
                return None
        finally:
            self.limiter.release()

@inject
async def scrape_websites(scraper: Scraper, logger: Logger):
    urls = [
        "https://example.com",
        "https://example.org",
        "https://example.net"
    ]
    
    results = await asyncio.gather(*[
        scraper.scrape(url) for url in urls
    ])
    
    logger.info(f"Scraped {len([r for r in results if r])} pages")

if __name__ == "__main__":
    asyncio.run(scrape_websites())
```

## Task Queue System

Sistema de cola de tareas con workers y prioridades.

```python
import asyncio
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any
from R5.background import Background
from R5.ioc import singleton, inject

class Priority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class Task:
    id: int
    name: str
    handler: Callable
    args: tuple
    kwargs: dict
    priority: Priority

@singleton
class TaskQueue:
    def __init__(self):
        self.tasks: list[Task] = []
        self.completed: list[int] = []
    
    def add_task(
        self,
        name: str,
        handler: Callable,
        priority: Priority = Priority.NORMAL,
        *args,
        **kwargs
    ):
        task = Task(
            id=len(self.tasks) + 1,
            name=name,
            handler=handler,
            args=args,
            kwargs=kwargs,
            priority=priority
        )
        self.tasks.append(task)
        return task.id
    
    def get_next_task(self) -> Optional[Task]:
        pending = [t for t in self.tasks if t.id not in self.completed]
        if not pending:
            return None
        
        # Sort by priority
        pending.sort(key=lambda t: t.priority.value, reverse=True)
        return pending[0]
    
    def mark_completed(self, task_id: int):
        self.completed.append(task_id)

@singleton
class Worker:
    def __init__(self, queue: TaskQueue, logger: Logger):
        self.queue = queue
        self.logger = logger
    
    async def process_task(self, task: Task):
        self.logger.info(
            f"Processing task {task.id}: {task.name} "
            f"(Priority: {task.priority.name})"
        )
        
        try:
            result = task.handler(*task.args, **task.kwargs)
            if asyncio.iscoroutine(result):
                await result
            
            self.queue.mark_completed(task.id)
            self.logger.info(f"Task {task.id} completed")
        except Exception as e:
            self.logger.error(f"Task {task.id} failed: {e}")

@inject
async def run_workers(
    bg: Background,
    queue: TaskQueue,
    worker: Worker,
    logger: Logger
):
    # Add tasks
    queue.add_task("send_email", send_email, Priority.HIGH, "user@example.com")
    queue.add_task("process_image", process_image, Priority.NORMAL, "image.jpg")
    queue.add_task("cleanup", cleanup_temp, Priority.LOW)
    queue.add_task("critical_alert", send_alert, Priority.CRITICAL, "System down")
    
    # Process tasks
    while True:
        task = queue.get_next_task()
        if not task:
            break
        
        await bg.add(worker.process_task, task)
    
    await asyncio.sleep(2)
    logger.info("All tasks processed")

def send_email(to: str):
    print(f"Sending email to {to}")

def process_image(filename: str):
    print(f"Processing image: {filename}")

def cleanup_temp():
    print("Cleaning up temp files")

def send_alert(message: str):
    print(f"ALERT: {message}")

if __name__ == "__main__":
    asyncio.run(run_workers())
```

## Microservicio API Gateway

Gateway que enruta requests a múltiples servicios.

```python
import asyncio
from dataclasses import dataclass
from typing import Optional
from R5.http import Http
from R5.ioc import singleton, inject, config

@config(file='.env')
class GatewayConfig:
    user_service_url: str = "http://localhost:8001"
    order_service_url: str = "http://localhost:8002"
    payment_service_url: str = "http://localhost:8003"

@dataclass
class ServiceResponse:
    service: str
    status: int
    data: dict

@singleton
class ServiceRegistry:
    def __init__(self, config: GatewayConfig):
        self.services = {
            "users": config.user_service_url,
            "orders": config.order_service_url,
            "payments": config.payment_service_url
        }
    
    def get_url(self, service: str) -> Optional[str]:
        return self.services.get(service)

@singleton
class Gateway:
    def __init__(
        self,
        http: Http,
        registry: ServiceRegistry,
        logger: Logger
    ):
        self.http = http
        self.registry = registry
        self.logger = logger
    
    async def route(
        self,
        service: str,
        endpoint: str,
        method: str = "GET",
        **kwargs
    ) -> ServiceResponse:
        base_url = self.registry.get_url(service)
        if not base_url:
            self.logger.error(f"Service not found: {service}")
            return ServiceResponse(service, 404, {"error": "Service not found"})
        
        url = f"{base_url}{endpoint}"
        self.logger.info(f"Routing to {service}: {method} {url}")
        
        if method == "GET":
            result = await self.http.get(url, **kwargs)
        elif method == "POST":
            result = await self.http.post(url, **kwargs)
        else:
            return ServiceResponse(service, 405, {"error": "Method not allowed"})
        
        return ServiceResponse(
            service=service,
            status=result.status,
            data=result.to(dict) or {}
        )

@inject
async def gateway_example(gateway: Gateway, logger: Logger):
    # Route to user service
    user_response = await gateway.route("users", "/users/1")
    logger.info(f"User service: {user_response.status}")
    
    # Route to order service
    order_response = await gateway.route(
        "orders",
        "/orders",
        method="POST",
        json={"user_id": 1, "amount": 99.99}
    )
    logger.info(f"Order service: {order_response.status}")

if __name__ == "__main__":
    asyncio.run(gateway_example())
```

## Sistema de Notificaciones

Sistema multi-canal de notificaciones (email, SMS, push).

```python
import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from R5.ioc import singleton, inject
from R5.background import Background

class Channel(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

@dataclass
class Notification:
    channel: Channel
    recipient: str
    message: str
    priority: int = 0

class NotificationProvider(ABC):
    @abstractmethod
    async def send(self, recipient: str, message: str):
        pass

@singleton
class EmailProvider(NotificationProvider):
    async def send(self, recipient: str, message: str):
        print(f"📧 Email to {recipient}: {message}")
        await asyncio.sleep(0.1)

@singleton
class SMSProvider(NotificationProvider):
    async def send(self, recipient: str, message: str):
        print(f"📱 SMS to {recipient}: {message}")
        await asyncio.sleep(0.1)

@singleton
class PushProvider(NotificationProvider):
    async def send(self, recipient: str, message: str):
        print(f"🔔 Push to {recipient}: {message}")
        await asyncio.sleep(0.1)

@singleton
class NotificationService:
    def __init__(
        self,
        email: EmailProvider,
        sms: SMSProvider,
        push: PushProvider,
        logger: Logger
    ):
        self.providers = {
            Channel.EMAIL: email,
            Channel.SMS: sms,
            Channel.PUSH: push
        }
        self.logger = logger
    
    async def send(self, notification: Notification):
        provider = self.providers.get(notification.channel)
        if not provider:
            self.logger.error(f"Invalid channel: {notification.channel}")
            return
        
        self.logger.info(
            f"Sending {notification.channel.value} notification "
            f"to {notification.recipient}"
        )
        
        try:
            await provider.send(notification.recipient, notification.message)
            self.logger.info(f"Notification sent successfully")
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")

@inject
async def send_notifications(
    bg: Background,
    notif_service: NotificationService
):
    notifications = [
        Notification(Channel.EMAIL, "user@example.com", "Welcome!"),
        Notification(Channel.SMS, "+1234567890", "Your code: 123456"),
        Notification(Channel.PUSH, "device_token_123", "New message"),
    ]
    
    for notif in notifications:
        await bg.add(notif_service.send, notif)
    
    await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(send_notifications())
```

## Event-Driven Architecture

Sistema basado en eventos con suscriptores.

```python
import asyncio
from dataclasses import dataclass
from typing import Callable
from R5.ioc import singleton, inject
from R5.background import Background

@dataclass
class Event:
    type: str
    data: dict

@singleton
class EventBus:
    def __init__(self):
        self.subscribers: dict[str, list[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
    
    async def publish(self, bg: Background, event: Event):
        if event.type not in self.subscribers:
            return
        
        for handler in self.subscribers[event.type]:
            await bg.add(handler, event=event)

# Event Handlers
def on_user_registered(logger: Logger, event: Event):
    logger.info(f"User registered: {event.data['email']}")

def send_welcome_email(email_service: EmailService, event: Event):
    email_service.send(
        event.data["email"],
        "Welcome!",
        "Thanks for registering"
    )

def create_default_profile(logger: Logger, event: Event):
    logger.info(f"Creating profile for {event.data['username']}")

@inject
async def event_driven_example(bg: Background, event_bus: EventBus):
    # Subscribe to events
    event_bus.subscribe("user.registered", on_user_registered)
    event_bus.subscribe("user.registered", send_welcome_email)
    event_bus.subscribe("user.registered", create_default_profile)
    
    # Publish event
    event = Event(
        type="user.registered",
        data={
            "username": "john_doe",
            "email": "john@example.com"
        }
    )
    
    await event_bus.publish(bg, event)
    await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(event_driven_example())
```

## Próximos Pasos

- [Simple Examples](simple.md) - Ejemplos básicos
- [Patterns](patterns.md) - Patrones de diseño con R5
- [API Reference](../api/ioc.md) - Documentación de la API
