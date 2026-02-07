# R5 Framework

**Framework moderno de Python con Inyección de Dependencias, Cliente HTTP y Tareas en Background**

[![Python Version](https://img.shields.io/badge/python-3.14%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-active-success)](https://github.com/henryjaimesR5/R5)

---

## ¿Qué es R5?

R5 es un framework ligero y modular para Python que proporciona tres componentes fundamentales:

- 🔌 **IoC Container** - Inyección de dependencias automática y type-safe
- 🌐 **HTTP Client** - Cliente HTTP asíncrono con pooling, retry y Result pattern
- ⚡ **Background Tasks** - Sistema de ejecución de tareas concurrentes con anyio

## Características Principales

### ✨ Inyección de Dependencias Simple

```python
from R5.ioc import singleton, inject

@singleton
class UserService:
    def get_user(self, user_id: int):
        return {"id": user_id, "name": "John"}

@inject
async def process_user(service: UserService, user_id: int):
    return service.get_user(user_id)

user = await process_user(user_id=1)
```

### 🚀 Cliente HTTP Poderoso

```python
from R5.http import Http
from R5.ioc import inject

@inject
async def fetch_data(http: Http):
    result = await http.get("https://api.example.com/users/1")
    user = result.to(UserDTO)
    return user
```

### 🔄 Background Tasks Integradas

```python
from R5.background import Background
from R5.ioc import inject

@inject
async def queue_tasks(bg: Background):
    await bg.add(send_email, "user@example.com")
    await bg.add(process_payment, payment_id)
    await bg.add(update_cache, cache_key)
```

## ¿Por qué R5?

### 🎯 Simple y Directo

Sin configuración complicada. Usa decoradores simples como `@singleton`, `@inject` y empieza a trabajar inmediatamente.

### 🔒 Type-Safe

Aprovecha el sistema de tipos de Python para inyección automática y detección temprana de errores.

### ⚡ Alto Rendimiento

- Connection pooling automático en HTTP client
- Tareas concurrentes con anyio
- Recursos gestionados con context managers

### 🧩 Modular

Usa solo lo que necesitas. Cada módulo funciona independientemente:

- `R5.ioc` - Container e inyección
- `R5.http` - Cliente HTTP
- `R5.background` - Tareas background

### 🎨 Patrones Modernos

- **Result Pattern** para manejo de errores
- **Resource Pattern** para lifecycle management
- **Builder Pattern** para configuración fluida

## Instalación Rápida

```bash
# Con pip
pip install r5

# Con uv
uv add r5
```

## Ejemplo Completo

```python
import asyncio
from dataclasses import dataclass
from R5.ioc import singleton, inject, config
from R5.http import Http
from R5.background import Background

@config(file='.env')
class AppConfig:
    api_url: str = "https://api.example.com"
    api_key: str = ""

@singleton
class EmailService:
    async def send(self, to: str, subject: str):
        print(f"Sending email to {to}: {subject}")

@dataclass
class UserDTO:
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
    result = await http.get(f"{config.api_url}/users/1")
    user = result.to(UserDTO)
    
    if user:
        await bg.add(email.send, user.email, "Welcome!")
        print(f"User: {user.name}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Próximos Pasos

<div class="grid cards" markdown>

- :material-clock-fast: **[Quick Start](getting-started/quickstart.md)**

    Empieza a usar R5 en minutos

- :material-book-open-variant: **[Guías](guides/ioc/overview.md)**

    Aprende los conceptos fundamentales

- :material-api: **[API Reference](api/ioc.md)**

    Documentación completa de la API

</div>

## Licencia

MIT License - Libre para uso personal y comercial.
