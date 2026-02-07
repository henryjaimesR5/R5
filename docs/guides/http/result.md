# Result Pattern

El `Result` encapsula respuestas HTTP, permitiendo manejo de errores sin excepciones.

## Propiedades

- `response` - La respuesta HTTP (`None` si hubo excepción)
- `request` - La request original
- `status` - Código de estado HTTP (`0` si hubo excepción)
- `exception` - Excepción capturada (`None` si fue exitosa)

## Creación

```python
from R5.http import Result
import httpx

# Desde response
response = httpx.Response(200, json={"id": 1, "name": "John"})
result = Result.from_response(response)

# Desde excepción
result = Result.from_exception(Exception("Network error"))
# result.status == 0, result.response == None
```

## Verificación de Estado

```python
@inject
async def check_status(http: Http):
    result = await http.get("https://api.example.com/users/1")

    if result.exception:
        print(f"Request failed: {result.exception}")
        return None

    if result.status == 200:
        return result.to(User)
    elif result.status == 404:
        print("Not found")
    elif result.status >= 500:
        print("Server error")
```

## Handlers Encadenados

Los handlers ejecutan side effects sin modificar el result. Retornan `self` para chaining:

```python
@inject
async def chained_handlers(http: Http):
    result = await http.get("https://api.example.com/users/1")

    user = (result
        .on_status(404, lambda req, res: print("Not found"))
        .on_status(500, lambda req, res: print("Server error"))
        .on_exception(lambda e: log_error(e))
        .to(User))

    return user
```

## Mapeo a Tipos con `to()`

Convierte la respuesta JSON al tipo especificado. Retorna `None` si falla:

```python
from pydantic import BaseModel
from dataclasses import dataclass
from typing import TypedDict

# Pydantic (con validación automática)
class User(BaseModel):
    id: int
    name: str
    email: str

user = result.to(User)

# Dataclass
@dataclass
class Product:
    id: int
    name: str
    price: float

product = result.to(Product)

# Dict, List, TypedDict
data = result.to(dict)
items = result.to(list)
```

### Validación de Nulos en Dataclasses

R5 valida que valores `None` del JSON sean compatibles con los type hints. Si un campo recibe `None` pero no es `Optional`, se emite un `UserWarning`:

```python
@dataclass
class Product:
    id: int
    name: str                    # No Optional → warning si es None
    description: Optional[str]   # Optional → sin warning

# JSON: {"id": 1, "name": null, "description": null}
product = result.to(Product)
# ⚠️ UserWarning: Fields ['name'] have None values but are not typed as Optional in Product
```

| Tipo Destino | Validación de nulos |
|---|---|
| `@dataclass` | Activa |
| `Pydantic BaseModel` | Delegada a Pydantic |
| `dict` / `list` / `TypedDict` | Inactiva |

## Manejo de Errores

```python
@inject
async def safe_fetch(http: Http):
    result = await http.get("https://api.example.com/data")

    user = result.to(User)
    if user is None:
        # Fallo en mapping: JSON inválido, tipo incompatible, o error de red
        print(f"Status: {result.status}")
        return {"default": True}  # fallback

    return user
```

## Acceso a Response/Request

```python
if result.response:
    print(result.response.headers)
    print(result.response.text)
    print(result.response.json())

if result.request:
    print(result.request.url)
    print(result.request.method)
```

## Próximos Pasos

- [Basic Usage](basic-usage.md) - Uso básico del cliente
- [Advanced](advanced.md) - Retry, proxy rotation, handlers globales
