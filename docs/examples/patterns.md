# Patrones de Diseño con R5

Patrones que aprovechan las capacidades específicas de R5.

## Repository + Service Layer

```python
from abc import ABC, abstractmethod
from R5.ioc import singleton, inject

class IUserRepository(ABC):
    @abstractmethod
    def find(self, user_id: int) -> dict | None: ...
    @abstractmethod
    def save(self, user: dict) -> dict: ...

@singleton
class UserRepository(IUserRepository):
    def __init__(self, db: DatabaseService, logger: Logger):
        self.db = db
        self.logger = logger

    def find(self, user_id: int):
        self.logger.info(f"Finding user {user_id}")
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

    def save(self, user: dict):
        self.db.execute("INSERT INTO users ...")
        return user

@singleton
class UserService:
    def __init__(self, repo: IUserRepository, email: EmailService):
        self.repo = repo
        self.email = email

    async def register(self, username: str, email_addr: str):
        user = self.repo.save({"username": username, "email": email_addr})
        await self.email.send(email_addr, "Welcome", "Thanks for joining!")
        return user

# Intercambiar implementación via alias
Container.alias_provider(IUserRepository, UserRepository)
```

## Observer / Event Bus

Patrón especialmente útil con Background tasks para procesamiento asíncrono de eventos:

```python
@singleton
class EventBus:
    def __init__(self):
        self.subscribers: dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        self.subscribers.setdefault(event_type, []).append(handler)

    async def publish(self, bg: Background, event_type: str, data: dict):
        for handler in self.subscribers.get(event_type, []):
            await bg.add(handler, data=data)

# Handlers reciben dependencias via IoC
def on_user_registered(logger: Logger, data: dict):
    logger.info(f"User registered: {data['email']}")

def send_welcome(email: EmailService, data: dict):
    email.send(data["email"], "Welcome!", "Thanks!")

@inject
async def main(bg: Background, bus: EventBus):
    bus.subscribe("user.registered", on_user_registered)
    bus.subscribe("user.registered", send_welcome)

    await bus.publish(bg, "user.registered", {"email": "john@example.com"})
    await asyncio.sleep(1)
```

## Unit of Work (Resource scope)

Aprovecha `@resource` para transacciones con commit/rollback automático:

```python
@resource
class UnitOfWork:
    def __init__(self, db: DatabaseService):
        self.db = db

    async def __aenter__(self):
        await self.db.begin_transaction()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.db.rollback()
        else:
            await self.db.commit()

@inject
async def create_order(uow: UnitOfWork):
    # Si algo falla, se hace rollback automáticamente
    uow.db.execute("INSERT INTO orders ...")
    uow.db.execute("UPDATE inventory ...")
```

## Strategy con IoC

```python
class PaymentStrategy(ABC):
    @abstractmethod
    async def process(self, amount: float) -> bool: ...

@singleton
class CreditCardPayment(PaymentStrategy):
    async def process(self, amount: float) -> bool:
        print(f"Credit Card: ${amount}")
        return True

@singleton
class PayPalPayment(PaymentStrategy):
    async def process(self, amount: float) -> bool:
        print(f"PayPal: ${amount}")
        return True

@singleton
class PaymentService:
    def __init__(self, cc: CreditCardPayment, paypal: PayPalPayment):
        self.strategies = {"credit_card": cc, "paypal": paypal}

    async def pay(self, method: str, amount: float):
        strategy = self.strategies.get(method)
        if not strategy:
            raise ValueError(f"Unknown method: {method}")
        return await strategy.process(amount)
```

## Saga Pattern

Para transacciones distribuidas con compensación:

```python
@dataclass
class SagaStep:
    action: Callable
    compensate: Callable

@singleton
class SagaOrchestrator:
    def __init__(self, logger: Logger):
        self.logger = logger

    async def execute(self, steps: list[SagaStep]):
        executed = []
        try:
            for step in steps:
                await step.action()
                executed.append(step)
        except Exception as e:
            self.logger.error(f"Saga failed: {e}")
            for step in reversed(executed):
                await step.compensate()
            raise
```

## Próximos Pasos

- [Ejemplos simples](simple.md) - Ejemplos básicos
- [Ejemplos reales](real-world.md) - Aplicaciones completas
