# Configuration

El decorador `@config` carga valores desde archivos y variables de entorno, los convierte a los tipos correctos, y registra la clase como Singleton en el container.

## Uso Básico

```python
from R5.ioc import config

@config(file='.env')
class AppConfig:
    database_url: str = "sqlite:///app.db"
    api_key: str = ""
    debug: bool = False
    port: int = 8000
```

Se inyecta automáticamente:

```python
@inject
async def main(config: AppConfig):
    print(config.database_url)
```

## Formatos Soportados

| Formato | Extensión | Ejemplo |
|---|---|---|
| Variables de entorno | `.env` | `DATABASE_URL=postgres://...` |
| JSON | `.json` | `{"database_url": "..."}` |
| YAML | `.yml` / `.yaml` | `database_url: postgres://...` |
| Properties | `.properties` | `database.url=postgres://...` |

```python
@config(file='config.json')   # o .yml, .env, .properties
class AppConfig:
    database_url: str
    port: int
```

En `.env`, las listas se separan por comas: `ALLOWED_HOSTS=localhost,example.com`

## Conversión de Tipos

R5 convierte strings a los tipos indicados por los type hints:

```python
@config(file='.env')
class Config:
    app_name: str = "MyApp"
    port: int = 8000
    timeout: float = 30.5
    debug: bool = False              # true/false/1/0/yes/no/on/off
    allowed_hosts: list[str] = ["localhost"]
    metadata: dict[str, str] = {}
```

## Variables de Entorno Override

Por defecto las variables de entorno tienen prioridad sobre el archivo:

```python
@config(file='config.json', env_override=True)  # default
class AppConfig:
    port: int = 8000
```

**Prioridad**: Variables de entorno > Archivo > Defaults de la clase

Deshabilitar: `env_override=False`

## Opciones

```python
@config(
    file='.env',
    required=True,          # FileNotFoundError si no existe (default: True)
    env_override=True,      # Variables de entorno tienen prioridad (default: True)
    case_sensitive=False     # Claves case-insensitive (default: False)
)
class Config: ...
```

Sin archivo (solo defaults):

```python
@config
class Config:
    database_url: str = "sqlite:///app.db"
```

## Configuración Anidada

```python
@config(file='database.json')
class DatabaseConfig:
    url: str
    pool_size: int = 10

@config(file='redis.json')
class RedisConfig:
    host: str = "localhost"
    port: int = 6379

@singleton
class AppConfig:
    def __init__(self, db: DatabaseConfig, redis: RedisConfig):
        self.database = db
        self.redis = redis
```

## Validación con Pydantic

```python
from pydantic import BaseModel, field_validator

@config(file='.env')
class AppConfig(BaseModel):
    port: int

    @field_validator('port')
    def validate_port(cls, v):
        if v < 1 or v > 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
```

## Propiedades Computadas

```python
@config(file='.env')
class AppConfig:
    host: str = "localhost"
    port: int = 8000

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"
```

## Multi-Entorno

```python
import os

@config(file=f"config.{os.getenv('ENV', 'development')}.json")
class AppConfig:
    database_url: str
    debug: bool
```

## Warnings

- **Campo sin valor en ninguna fuente** → `UserWarning` + `None`
- **Archivo no encontrado con `required=False`** → `UserWarning` + usa defaults

## Próximos Pasos

- [Overview](overview.md) - IoC Container
- [Injection](injection.md) - `@inject`
- [Providers](providers.md) - Scopes
