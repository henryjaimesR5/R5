# Configuration

El decorador `@config` simplifica la gestión de configuración cargando valores desde archivos y variables de entorno.

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

El decorador:
1. Carga el archivo especificado
2. Mapea valores a los campos de la clase
3. Convierte tipos automáticamente
4. Permite override con variables de entorno
5. Registra la clase como Singleton en el container

## Formatos Soportados

R5 soporta múltiples formatos de configuración:

### .env (Variables de Entorno)

```env
# .env
DATABASE_URL=postgresql://localhost/mydb
API_KEY=secret-key-123
DEBUG=true
PORT=8080
MAX_WORKERS=4
```

```python
@config(file='.env')
class AppConfig:
    database_url: str
    api_key: str
    debug: bool
    port: int
    max_workers: int
```

### JSON

```json
{
  "database_url": "postgresql://localhost/mydb",
  "api_key": "secret-key-123",
  "debug": true,
  "port": 8080,
  "max_workers": 4
}
```

```python
@config(file='config.json')
class AppConfig:
    database_url: str
    api_key: str
    debug: bool
    port: int
    max_workers: int
```

### YAML

```yaml
database_url: postgresql://localhost/mydb
api_key: secret-key-123
debug: true
port: 8080
max_workers: 4
features:
  - auth
  - cache
  - logging
```

```python
@config(file='config.yml')
class AppConfig:
    database_url: str
    api_key: str
    debug: bool
    port: int
    max_workers: int
    features: list[str]
```

### Properties (Java-style)

```properties
# config.properties
database.url=postgresql://localhost/mydb
api.key=secret-key-123
debug=true
port=8080
```

```python
@config(file='config.properties')
class AppConfig:
    database_url: str  # Coincide con "database.url"
    api_key: str       # Coincide con "api.key"
    debug: bool
    port: int
```

## Conversión de Tipos

R5 convierte automáticamente strings a los tipos correctos:

### Tipos Primitivos

```python
@config(file='.env')
class Config:
    # String
    app_name: str = "MyApp"
    
    # Integer
    port: int = 8000
    
    # Float
    timeout: float = 30.5
    
    # Boolean (true, false, 1, 0, yes, no, on, off)
    debug: bool = False
```

**Archivo .env:**
```env
APP_NAME=ProductionApp
PORT=9000
TIMEOUT=45.5
DEBUG=true
```

### Colecciones

```python
@config(file='config.json')
class Config:
    # List
    allowed_hosts: list[str] = ["localhost"]
    
    # Set
    features: set[str] = {"auth", "cache"}
    
    # Tuple
    coordinates: tuple[float, float] = (0.0, 0.0)
    
    # Dict
    metadata: dict[str, str] = {}
```

**Archivo JSON:**
```json
{
  "allowed_hosts": ["localhost", "example.com", "app.com"],
  "features": ["auth", "cache", "logging"],
  "coordinates": [40.7128, 74.0060],
  "metadata": {
    "version": "1.0",
    "env": "production"
  }
}
```

### Listas desde .env

En archivos .env, las listas se separan por comas:

```env
ALLOWED_HOSTS=localhost,example.com,app.com
FEATURES=auth,cache,logging
```

```python
@config(file='.env')
class Config:
    allowed_hosts: list[str]  # ["localhost", "example.com", "app.com"]
    features: list[str]        # ["auth", "cache", "logging"]
```

## Variables de Entorno Override

Por defecto, las variables de entorno tienen prioridad sobre el archivo:

```python
@config(file='config.json', env_override=True)
class AppConfig:
    port: int = 8000
```

**Prioridad (de mayor a menor):**
1. Variables de entorno (ej: `PORT=9000`)
2. Archivo de configuración
3. Valores por defecto en la clase

**Ejemplo:**
```bash
# config.json tiene "port": 8080
# Clase tiene default port: int = 8000

# Sin variable de entorno
# → port = 8080 (del archivo)

export PORT=9000
# Con variable de entorno
# → port = 9000 (override)
```

### Deshabilitar override

```python
@config(file='config.json', env_override=False)
class AppConfig:
    port: int = 8000
```

Ahora las variables de entorno se ignoran.

## Case Sensitivity

Por defecto, las claves son case-insensitive:

```env
# .env
database_url=...
DATABASE_URL=...
Database_Url=...
# Todas coinciden con database_url
```

Para case-sensitive:

```python
@config(file='.env', case_sensitive=True)
class Config:
    database_url: str  # Solo coincide exactamente con "database_url"
```

## Archivos Opcionales

Si el archivo no existe, puedes:

**Requerir el archivo (default):**
```python
@config(file='config.json', required=True)
class Config:
    port: int = 8000

# Si config.json no existe → FileNotFoundError
```

**Hacer opcional:**
```python
@config(file='config.json', required=False)
class Config:
    port: int = 8000

# Si config.json no existe → usa valores por defecto
# Emite warning
```

## Sin Archivo

Usa solo valores por defecto:

```python
@config
class Config:
    database_url: str = "sqlite:///app.db"
    debug: bool = False
```

O con paréntesis vacíos:

```python
@config()
class Config:
    database_url: str = "sqlite:///app.db"
    debug: bool = False
```

## Inyección de Configuración

Una vez decorada, la configuración se inyecta automáticamente:

```python
from R5.ioc import inject

@config(file='.env')
class AppConfig:
    database_url: str
    api_key: str

@inject
async def main(config: AppConfig):
    print(f"Database: {config.database_url}")
    print(f"API Key: {config.api_key}")
```

## Configuración Anidada

Para configuraciones complejas, usa múltiples clases:

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

@inject
def use_config(config: AppConfig):
    print(config.database.url)
    print(config.redis.host)
```

## Validación con Pydantic

Combina con Pydantic para validación:

```python
from pydantic import BaseModel, field_validator

@config(file='.env')
class AppConfig(BaseModel):
    database_url: str
    port: int
    
    @field_validator('port')
    def validate_port(cls, v):
        if v < 1 or v > 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v

# Validación automática al crear instancia
```

## Valores Computados

Agrega propiedades computadas:

```python
@config(file='.env')
class AppConfig:
    host: str = "localhost"
    port: int = 8000
    
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

@inject
def use_config(config: AppConfig):
    print(config.base_url)  # "http://localhost:8000"
```

## Rutas Relativas

Las rutas se resuelven relativas al directorio de trabajo:

```python
# Archivo en ./config/app.json
@config(file='config/app.json')
class AppConfig:
    pass

# Archivo en ruta absoluta
@config(file='/etc/myapp/config.json')
class AppConfig:
    pass
```

## Ejemplos Completos

### Configuración de Aplicación Web

```python
@config(file='.env')
class AppConfig:
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # Database
    database_url: str = "postgresql://localhost/myapp"
    db_pool_size: int = 10
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # Auth
    secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Features
    debug: bool = False
    enable_cors: bool = True
    allowed_origins: list[str] = ["*"]
    
    @property
    def database_url_async(self) -> str:
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
```

### Configuración Multi-Entorno

```python
import os

env = os.getenv("ENV", "development")
config_file = f"config.{env}.json"

@config(file=config_file)
class AppConfig:
    database_url: str
    api_key: str
    debug: bool

# Carga config.development.json, config.production.json, etc.
```

### Configuración con Secretos

```env
# .env (commitear)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=myapp

# .env.local (no commitear, en .gitignore)
DATABASE_PASSWORD=super-secret-password
API_KEY=secret-api-key
```

```python
# Cargar .env primero, luego .env.local
@config(file='.env')
class BaseConfig:
    database_host: str
    database_port: int
    database_name: str

@config(file='.env.local', required=False)
class SecretConfig:
    database_password: str = ""
    api_key: str = ""

@singleton
class AppConfig:
    def __init__(self, base: BaseConfig, secrets: SecretConfig):
        self.db_url = (
            f"postgresql://{base.database_host}:{base.database_port}"
            f"/{base.database_name}"
        )
        if secrets.database_password:
            self.db_url = (
                f"postgresql://user:{secrets.database_password}"
                f"@{base.database_host}:{base.database_port}"
                f"/{base.database_name}"
            )
        self.api_key = secrets.api_key
```

## Caché de Configuración

R5 cachea automáticamente la configuración cargada del archivo usando `@lru_cache`:

```python
# Primera instancia: lee archivo
config1 = Container.resolve(AppConfig)

# Segunda instancia: usa caché
config2 = Container.resolve(AppConfig)

# Mismo archivo cacheado (Singleton + LRU cache)
```

## Warnings

### Campo sin valor

Si un campo no tiene valor en ninguna fuente:

```python
@config(file='.env')
class Config:
    required_field: str  # Sin default

# Si no está en .env ni variables de entorno
# → UserWarning + None
```

### Archivo no encontrado

```python
@config(file='missing.json', required=False)
class Config:
    port: int = 8000

# UserWarning: Configuration file missing.json not found. Using default values.
```

## Testing

### Mock de configuración

```python
def test_with_config():
    Container.reset()
    
    @config
    class TestConfig:
        database_url: str = "sqlite:///:memory:"
        debug: bool = True
    
    @inject
    def handler(config: TestConfig):
        assert config.debug
        return config.database_url
    
    result = handler()
    assert result == "sqlite:///:memory:"
```

### Configuración temporal

```python
import tempfile
import json

def test_with_temp_config():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
        config_data = {"port": 9999, "debug": True}
        json.dump(config_data, f)
        f.flush()
        
        @config(file=f.name)
        class TempConfig:
            port: int
            debug: bool
        
        config = Container.resolve(TempConfig)
        assert config.port == 9999
```

## Próximos Pasos

- [Overview](overview.md) - Conceptos del IoC Container
- [Injection](injection.md) - Guía de `@inject`
- [Providers](providers.md) - Scopes y decoradores
- [API Reference](../../api/ioc.md) - Documentación completa
