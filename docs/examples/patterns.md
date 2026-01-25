# Patrones de Diseño con R5

Patrones comunes implementados con R5.

## Repository Pattern

```python
from abc import ABC, abstractmethod
from typing import Optional
from R5.ioc import singleton, inject

class IUserRepository(ABC):
    @abstractmethod
    def find(self, user_id: int) -> Optional[dict]:
        pass
    
    @abstractmethod
    def save(self, user: dict) -> dict:
        pass

@singleton
class UserRepository(IUserRepository):
    def __init__(self, db: DatabaseService, logger: Logger):
        self.db = db
        self.logger = logger
    
    def find(self, user_id: int) -> Optional[dict]:
        self.logger.info(f"Finding user {user_id}")
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
    
    def save(self, user: dict) -> dict:
        self.logger.info(f"Saving user {user['id']}")
        self.db.execute(f"INSERT INTO users ...")
        return user

@singleton
class UserService:
    def __init__(self, repo: IUserRepository):
        self.repo = repo
    
    def get_user(self, user_id: int) -> Optional[dict]:
        return self.repo.find(user_id)
```

## Service Layer Pattern

```python
@singleton
class EmailService:
    async def send(self, to: str, subject: str, body: str):
        print(f"Sending email to {to}")

@singleton
class UserService:
    def __init__(self, repo: UserRepository, email: EmailService):
        self.repo = repo
        self.email = email
    
    async def register_user(self, username: str, email_addr: str):
        user = {"username": username, "email": email_addr}
        saved_user = self.repo.save(user)
        await self.email.send(email_addr, "Welcome", "Thanks for joining!")
        return saved_user
```

## Factory Pattern

```python
from enum import Enum

class DatabaseType(Enum):
    POSTGRES = "postgres"
    MYSQL = "mysql"
    SQLITE = "sqlite"

class DatabaseFactory:
    @staticmethod
    def create(db_type: DatabaseType):
        if db_type == DatabaseType.POSTGRES:
            return PostgresDatabase()
        elif db_type == DatabaseType.MYSQL:
            return MySQLDatabase()
        else:
            return SQLiteDatabase()

@singleton
class DatabaseService:
    def __init__(self, config: AppConfig):
        self.db = DatabaseFactory.create(config.database_type)
```

## Strategy Pattern

```python
from abc import ABC, abstractmethod

class PaymentStrategy(ABC):
    @abstractmethod
    async def process(self, amount: float) -> bool:
        pass

@singleton
class CreditCardPayment(PaymentStrategy):
    async def process(self, amount: float) -> bool:
        print(f"Processing ${amount} via Credit Card")
        return True

@singleton
class PayPalPayment(PaymentStrategy):
    async def process(self, amount: float) -> bool:
        print(f"Processing ${amount} via PayPal")
        return True

@singleton
class PaymentService:
    def __init__(
        self,
        credit_card: CreditCardPayment,
        paypal: PayPalPayment
    ):
        self.strategies = {
            "credit_card": credit_card,
            "paypal": paypal
        }
    
    async def process_payment(self, method: str, amount: float) -> bool:
        strategy = self.strategies.get(method)
        if not strategy:
            raise ValueError(f"Unknown payment method: {method}")
        return await strategy.process(amount)
```

## Observer Pattern

```python
from typing import List, Callable

@singleton
class EventManager:
    def __init__(self):
        self.observers: dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self.observers:
            self.observers[event_type] = []
        self.observers[event_type].append(callback)
    
    async def notify(self, bg: Background, event_type: str, data: dict):
        if event_type in self.observers:
            for callback in self.observers[event_type]:
                await bg.add(callback, data=data)

def on_order_created(logger: Logger, data: dict):
    logger.info(f"Order created: {data['order_id']}")

def send_order_confirmation(email: EmailService, data: dict):
    email.send(data["customer_email"], "Order Confirmed", "...")

@inject
async def setup_observers(event_manager: EventManager):
    event_manager.subscribe("order.created", on_order_created)
    event_manager.subscribe("order.created", send_order_confirmation)
```

## Command Pattern

```python
from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

class CreateUserCommand(Command):
    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email
    
    def execute(self, user_service: UserService):
        return user_service.create_user(self.username, self.email)

class DeleteUserCommand(Command):
    def __init__(self, user_id: int):
        self.user_id = user_id
    
    def execute(self, user_service: UserService):
        return user_service.delete_user(self.user_id)

@singleton
class CommandBus:
    async def dispatch(self, bg: Background, command: Command):
        await bg.add(command.execute)
```

## CQRS Pattern

```python
# Commands (Write)
@singleton
class UserCommandService:
    def __init__(self, repo: UserRepository, events: EventManager):
        self.repo = repo
        self.events = events
    
    async def create_user(self, bg: Background, username: str):
        user = {"id": 123, "username": username}
        self.repo.save(user)
        await self.events.notify(bg, "user.created", user)

# Queries (Read)
@singleton
class UserQueryService:
    def __init__(self, cache: CacheService, repo: UserRepository):
        self.cache = cache
        self.repo = repo
    
    def get_user(self, user_id: int) -> Optional[dict]:
        cached = self.cache.get(f"user:{user_id}")
        if cached:
            return cached
        
        user = self.repo.find(user_id)
        self.cache.set(f"user:{user_id}", user)
        return user
```

## Unit of Work Pattern

```python
@resource
class UnitOfWork:
    def __init__(self, db: DatabaseService):
        self.db = db
        self.changes = []
    
    async def __aenter__(self):
        await self.db.begin_transaction()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.db.rollback()
        else:
            await self.db.commit()
    
    def register_new(self, entity: dict):
        self.changes.append(("insert", entity))
    
    def register_dirty(self, entity: dict):
        self.changes.append(("update", entity))

@inject
async def use_unit_of_work(uow: UnitOfWork):
    user = {"id": 1, "name": "John"}
    uow.register_new(user)
    
    order = {"id": 1, "user_id": 1, "total": 99.99}
    uow.register_new(order)
    
    # Commit o rollback automático al salir
```

## Decorator Pattern

```python
from functools import wraps
import time

def timing_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper

def cache_decorator(func):
    cache = {}
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key in cache:
            return cache[key]
        result = await func(*args, **kwargs)
        cache[key] = result
        return result
    return wrapper

@singleton
class UserService:
    @timing_decorator
    @cache_decorator
    async def get_user(self, user_id: int):
        # Simulate expensive operation
        await asyncio.sleep(1)
        return {"id": user_id, "name": "John"}
```

## Builder Pattern

```python
@factory
class QueryBuilder:
    def __init__(self):
        self.query = ""
        self.params = []
        self.where_clauses = []
    
    def select(self, *fields):
        self.query = f"SELECT {', '.join(fields)}"
        return self
    
    def from_table(self, table: str):
        self.query += f" FROM {table}"
        return self
    
    def where(self, condition: str, *params):
        self.where_clauses.append(condition)
        self.params.extend(params)
        return self
    
    def build(self):
        if self.where_clauses:
            self.query += " WHERE " + " AND ".join(self.where_clauses)
        return (self.query, self.params)

@inject
def use_builder(builder: QueryBuilder):
    query, params = (builder
        .select("id", "name", "email")
        .from_table("users")
        .where("age > ?", 18)
        .where("active = ?", True)
        .build())
    
    print(query)
    print(params)
```

## Saga Pattern

```python
from typing import List, Callable

@dataclass
class SagaStep:
    action: Callable
    compensate: Callable

@singleton
class SagaOrchestrator:
    def __init__(self, logger: Logger):
        self.logger = logger
    
    async def execute(self, steps: List[SagaStep]):
        executed = []
        
        try:
            for step in steps:
                self.logger.info(f"Executing step: {step.action.__name__}")
                await step.action()
                executed.append(step)
        except Exception as e:
            self.logger.error(f"Saga failed: {e}")
            # Compensate in reverse order
            for step in reversed(executed):
                self.logger.info(f"Compensating: {step.compensate.__name__}")
                await step.compensate()
            raise

# Usage
async def create_order():
    print("Creating order")

async def rollback_order():
    print("Rolling back order")

async def reserve_inventory():
    print("Reserving inventory")

async def release_inventory():
    print("Releasing inventory")

async def process_payment():
    print("Processing payment")
    raise Exception("Payment failed")

async def refund_payment():
    print("Refunding payment")

@inject
async def run_saga(saga: SagaOrchestrator):
    steps = [
        SagaStep(create_order, rollback_order),
        SagaStep(reserve_inventory, release_inventory),
        SagaStep(process_payment, refund_payment)
    ]
    
    try:
        await saga.execute(steps)
    except Exception:
        print("Saga completed with compensation")
```

## Adapter Pattern

```python
from abc import ABC, abstractmethod

class PaymentGateway(ABC):
    @abstractmethod
    async def charge(self, amount: float) -> bool:
        pass

# Third-party service
class StripeAPI:
    async def create_charge(self, cents: int):
        return {"status": "success"}

# Adapter
@singleton
class StripeAdapter(PaymentGateway):
    def __init__(self):
        self.stripe = StripeAPI()
    
    async def charge(self, amount: float) -> bool:
        cents = int(amount * 100)
        result = await self.stripe.create_charge(cents)
        return result["status"] == "success"

@singleton
class PaymentService:
    def __init__(self, gateway: PaymentGateway):
        self.gateway = gateway
    
    async def process_payment(self, amount: float) -> bool:
        return await self.gateway.charge(amount)
```

## Template Method Pattern

```python
from abc import ABC, abstractmethod

class DataProcessor(ABC):
    async def process(self, data: dict):
        validated = await self.validate(data)
        transformed = await self.transform(validated)
        result = await self.save(transformed)
        await self.notify(result)
        return result
    
    @abstractmethod
    async def validate(self, data: dict) -> dict:
        pass
    
    @abstractmethod
    async def transform(self, data: dict) -> dict:
        pass
    
    @abstractmethod
    async def save(self, data: dict) -> dict:
        pass
    
    async def notify(self, result: dict):
        print(f"Processing complete: {result}")

@singleton
class UserDataProcessor(DataProcessor):
    async def validate(self, data: dict) -> dict:
        if "email" not in data:
            raise ValueError("Email required")
        return data
    
    async def transform(self, data: dict) -> dict:
        data["email"] = data["email"].lower()
        return data
    
    async def save(self, data: dict) -> dict:
        # Save to database
        return data
```

## Chain of Responsibility

```python
from abc import ABC, abstractmethod
from typing import Optional

class Handler(ABC):
    def __init__(self):
        self.next_handler: Optional[Handler] = None
    
    def set_next(self, handler: 'Handler') -> 'Handler':
        self.next_handler = handler
        return handler
    
    async def handle(self, request: dict) -> Optional[dict]:
        result = await self.process(request)
        if result:
            return result
        
        if self.next_handler:
            return await self.next_handler.handle(request)
        
        return None
    
    @abstractmethod
    async def process(self, request: dict) -> Optional[dict]:
        pass

@singleton
class AuthenticationHandler(Handler):
    async def process(self, request: dict) -> Optional[dict]:
        if "token" not in request:
            return {"error": "Authentication required"}
        return None

@singleton
class AuthorizationHandler(Handler):
    async def process(self, request: dict) -> Optional[dict]:
        if request.get("role") != "admin":
            return {"error": "Insufficient permissions"}
        return None

@singleton
class ValidationHandler(Handler):
    async def process(self, request: dict) -> Optional[dict]:
        if "data" not in request:
            return {"error": "Invalid request"}
        return None

@inject
async def setup_chain(
    auth: AuthenticationHandler,
    authz: AuthorizationHandler,
    validate: ValidationHandler
):
    auth.set_next(authz).set_next(validate)
    
    request = {"token": "abc", "role": "admin", "data": {}}
    result = await auth.handle(request)
    
    if result:
        print(f"Request rejected: {result}")
    else:
        print("Request approved")
```

## Próximos Pasos

- [Simple Examples](simple.md) - Ejemplos básicos
- [Real World](real-world.md) - Aplicaciones completas
- [API Reference](../api/ioc.md) - Documentación de la API
