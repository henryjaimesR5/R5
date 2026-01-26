# R5 Framework

**Framework moderno de Python con Inyección de Dependencias, Cliente HTTP y Tareas en Background**

[![Python Version](https://img.shields.io/badge/python-3.14%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://r5.dev)
[![GitHub](https://img.shields.io/badge/github-repo-black)](https://github.com/henryjaimesR5/R5)


---

## ¿Qué es R5?

R5 es un framework ligero y modular para Python que proporciona tres componentes fundamentales para desarrollo moderno:

- 🔌 **IoC Container** - Inyección de dependencias automática y type-safe
- 🌐 **HTTP Client** - Cliente HTTP asíncrono con pooling, retry y Result pattern
- ⚡ **Background Tasks** - Sistema de ejecución de tareas concurrentes con anyio

## Características Principales

### ✨ Simple y Directo

Sin configuración complicada. Usa decoradores simples y empieza a trabajar:

```python
from R5.ioc import singleton, inject

@singleton
class UserService:
    def get_user(self, user_id: int):
        return {"id": user_id, "name": "John"}

@inject
async def process_user(service: UserService, user_id: int):
    return service.get_user(user_id)
```

### 🚀 Alto Rendimiento

- Connection pooling automático en HTTP client
- Tareas concurrentes con anyio
- Recursos gestionados con context managers

### 🔒 Type-Safe

Aprovecha el sistema de tipos de Python para inyección automática:

```python
@inject
async def handler(
    http: Http,              # Inyectado automáticamente
    bg: Background,          # Inyectado automáticamente
    config: AppConfig,       # Inyectado automáticamente
    user_id: int             # Parámetro manual
):
    pass
```

## Instalación

### Con uv (Recomendado)

```bash
uv add r5
```

### Con pip

```bash
pip install r5
```

## Quick Start

### 1. IoC - Inyección de Dependencias

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

### 2. HTTP Client

```python
from dataclasses import dataclass
from R5.http import Http
from R5.ioc import inject

@dataclass
class User:
    id: int
    name: str
    email: str

@inject
async def fetch_user(http: Http):
    result = await http.get("https://jsonplaceholder.typicode.com/users/1")
    user = result.to(User)
    
    if user:
        print(f"User: {user.name} ({user.email})")
```

### 3. Background Tasks

```python
from R5.background import Background
from R5.ioc import inject

def send_email(to: str):
    print(f"Sending email to {to}")

@inject
async def main(bg: Background):
    await bg.add(send_email, "user@example.com")
    await bg.add(send_email, "admin@example.com")
    
    await asyncio.sleep(0.5)
```

### 4. Todo Integrado

```python
import asyncio
from dataclasses import dataclass
from R5.ioc import singleton, inject, config
from R5.http import Http
from R5.background import Background

@config(file='.env')
class AppConfig:
    api_url: str = "https://api.example.com"

@singleton
class EmailService:
    async def send(self, to: str, subject: str):
        print(f"Sending email to {to}: {subject}")

@dataclass
class User:
    id: int
    name: str
    email: str

@inject
async def main(
    config: AppConfig,
    http: Http,
    bg: Background,
    email: EmailService
):
    # HTTP request
    result = await http.get(f"{config.api_url}/users/1")
    user = result.to(User)
    
    if user:
        # Background task
        await bg.add(email.send, user.email, "Welcome!")
        print(f"User: {user.name}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Características Detalladas

### IoC Container

- **Scopes**: Singleton, Factory, Resource
- **Inyección automática** basada en type hints
- **Configuración multi-formato**: .env, JSON, YAML, Properties
- **Detección de ciclos** en dependencias
- **Type-safe** en tiempo de desarrollo

```python
from R5.ioc import singleton, factory, resource, config

@singleton
class DatabaseConnection:
    pass

@factory
class Request:
    pass

@resource
class FileHandler:
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass

@config(file='config.json')
class AppConfig:
    database_url: str
    api_key: str
```

### HTTP Client

- **Connection pooling** con httpx
- **Result pattern** para manejo de errores sin excepciones
- **Retry automático** configurable
- **Handlers** para logging y métricas
- **Mapeo automático** a DTOs (Pydantic, dataclasses)
- **Validación de nulos** en campos no-opcionales

```python
from R5.http import Http
from R5.ioc import inject

@inject
async def fetch_data(http: Http):
    # Simple request
    result = await http.get("https://api.example.com/users/1")
    
    # Con retry
    result = await http.retry(
        attempts=3,
        delay=1.0,
        when_status=(429, 500, 502, 503)
    ).get("https://api.example.com/data")
    
    # Mapeo a DTO
    user = result.to(UserDTO)
```

#### Validación de Valores Nulos

R5 valida automáticamente campos con valores `None` al mapear a dataclasses. Si un campo tiene valor `None` pero no está tipificado como `Optional`, se emite un `UserWarning` indicando la inconsistencia:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Product:
    id: int
    name: str                    # No es Optional
    description: Optional[str]   # Es Optional

# JSON: {"id": 1, "name": null, "description": null}
result = await http.get("https://api.example.com/products/1")
product = result.to(Product)

# ⚠️ UserWarning: Fields ['name'] have None values but are not typed as Optional in Product
# El mapeo continúa normalmente, permitiendo detectar inconsistencias sin romper la funcionalidad
```

Esto ayuda a detectar problemas de tipado entre tu API y tus modelos, manteniendo la robustez del código.

### Background Tasks

- **Ejecución concurrente** con anyio
- **Thread pool** para tareas síncronas
- **Inyección IoC** en tareas
- **Error handling** robusto
- **Lifecycle management** automático

```python
from R5.background import Background
from R5.ioc import singleton, inject

@singleton
class Logger:
    def log(self, msg: str):
        print(f"[LOG] {msg}")

def background_task(logger: Logger, item_id: int):
    logger.log(f"Processing item {item_id}")

@inject
async def main(bg: Background):
    for i in range(10):
        await bg.add(background_task, item_id=i)
    
    await asyncio.sleep(1)
```

## Documentación

📚 **Documentación completa**: [https://r5.dev](https://r5.dev)

- [Installation](https://r5.dev/getting-started/installation)
- [Quick Start](https://r5.dev/getting-started/quickstart)
- [Core Concepts](https://r5.dev/getting-started/core-concepts)
- [IoC Container](https://r5.dev/guides/ioc/overview)
- [HTTP Client](https://r5.dev/guides/http/overview)
- [Background Tasks](https://r5.dev/guides/background/overview)
- [Examples](https://r5.dev/examples/simple)
- [API Reference](https://r5.dev/api/ioc)

### Build Docs Localmente

```bash
# Con make
make docs-serve

# Con uv directamente
uv run mkdocs serve

# Con script
./scripts/serve_docs.sh
```

Luego abre http://127.0.0.1:8000

## Ejemplos

Ver la carpeta [`examples.py`](examples.py) para ejemplos completos.

```bash
# Ejecutar ejemplos
uv run python examples.py

# O con make
make examples
```

## Testing

```bash
# Ejecutar tests
make test

# Con coverage
make test-cov

# Solo IoC tests
uv run pytest tests/ioc/

# Solo HTTP tests
uv run pytest tests/http/

# Solo Background tests
uv run pytest tests/background/
```

## Requisitos

- Python 3.14+
- uv (recomendado) o pip

## Dependencias

- `anyio` >= 4.12.0
- `dependency-injector` >= 4.48.3
- `httpx` >= 0.28.1
- `pydantic` >= 2.12.5
- `pydantic-settings` >= 2.12.0
- `pyyaml` >= 6.0.3

## Estructura del Proyecto

```
R5/
├── R5/
│   ├── ioc/           # IoC Container
│   │   ├── container.py
│   │   ├── providers.py
│   │   ├── injection.py
│   │   └── configuration.py
│   ├── http/          # HTTP Client
│   │   ├── http.py
│   │   ├── result.py
│   │   └── errors.py
│   └── background.py  # Background Tasks
├── tests/             # Tests
├── docs/              # Documentación
├── examples.py        # Ejemplos
└── pyproject.toml     # Configuración
```

## Contributing

¡Las contribuciones son bienvenidas! Ver [CONTRIBUTING.md](docs/contributing.md).

### Desarrollo

```bash
# Clonar repositorio
git clone https://github.com/grupor5/R5.git
cd R5

# Instalar dependencias
make install
make dev

# Ejecutar tests
make test

# Formato y lint
make format
make lint

# Build docs
make docs-serve
```

## Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

## Roadmap

- [ ] Publicar en PyPI
- [ ] GitHub Actions CI/CD
- [ ] Más ejemplos de integración
- [ ] Soporte para más formatos de config
- [ ] Plugin system
- [ ] Métricas y observabilidad integradas

## Agradecimientos

R5 usa las siguientes librerías excelentes:

- [httpx](https://www.python-httpx.org/) - Cliente HTTP
- [anyio](https://anyio.readthedocs.io/) - Concurrencia
- [dependency-injector](https://python-dependency-injector.ets-labs.org/) - Motor IoC
- [pydantic](https://pydantic-docs.helpmanual.io/) - Validación de datos

## Soporte

- 📧 Email: support@r5.dev
- 🐛 Issues: [GitHub Issues](https://github.com/grupor5/R5/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/grupor5/R5/discussions)

---

**R5** - Simple, Ligero, Poderoso 🚀
