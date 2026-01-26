# Result Pattern

El `Result` es un wrapper que encapsula respuestas HTTP, permitiendo manejo de errores sin excepciones.

## Concepto

En lugar de lanzar excepciones, R5 retorna un objeto `Result` que contiene:

- `response` - La respuesta HTTP (si existe)
- `request` - La request original (si existe)
- `status` - Código de estado HTTP (0 si hubo excepción)
- `exception` - Excepción capturada (None si fue exitosa)

## Creación de Result

### Desde Response

```python
from R5.http import Result
import httpx

response = httpx.Response(200, json={"id": 1, "name": "John"})
result = Result.from_response(response)

print(result.status)      # 200
print(result.exception)   # None
print(result.response)    # httpx.Response
```

### Desde Exception

```python
error = Exception("Network error")
result = Result.from_exception(error)

print(result.status)      # 0
print(result.exception)   # Exception("Network error")
print(result.response)    # None
```

## Verificación de Estado

### Por Status Code

```python
@inject
async def check_status(http: Http):
    result = await http.get("https://api.example.com/users/1")
    
    if result.status == 200:
        print("Success")
    elif result.status == 404:
        print("Not found")
    elif result.status >= 500:
        print("Server error")
```

### Por Rango

```python
@inject
async def check_range(http: Http):
    result = await http.get("https://api.example.com/data")
    
    if 200 <= result.status < 300:
        print("Success 2xx")
    elif 400 <= result.status < 500:
        print("Client error 4xx")
    elif 500 <= result.status < 600:
        print("Server error 5xx")
```

### Por Excepción

```python
@inject
async def check_exception(http: Http):
    result = await http.get("https://invalid-url.com")
    
    if result.exception:
        print(f"Request failed: {result.exception}")
        return None
    
    return result.to(dict)
```

## Handlers Encadenados

### on_status

Ejecuta handler si el status coincide:

```python
@inject
async def with_status_handler(http: Http):
    result = await http.get("https://api.example.com/users/1")
    
    result.on_status(404, lambda req, res: print("User not found"))
          .on_status(200, lambda req, res: print("User found"))
    
    # Los handlers NO modifican result, solo ejecutan side effects
```

### on_exception

Ejecuta handler si hubo excepción:

```python
@inject
async def with_exception_handler(http: Http):
    result = await http.get("https://api.example.com/data")
    
    result.on_exception(lambda e: print(f"Error: {e}"))
    
    # Continúa el flujo normal
    data = result.to(dict)
```

### Chaining

Los handlers retornan `self`, permitiendo chaining:

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

## Mapeo a Tipos

### to() Method

Convierte la respuesta JSON al tipo especificado:

```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str

@inject
async def map_to_user(http: Http):
    result = await http.get("https://api.example.com/users/1")
    
    # Mapea automáticamente
    user = result.to(User)
    
    if user:
        print(f"Name: {user.name}")
    else:
        print("Mapping failed")
```

### Tipos Soportados

#### Pydantic BaseModel

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str

result = await http.get("https://api.example.com/users/1")
user = result.to(User)  # Validación automática de Pydantic
```

#### Dataclass

```python
from dataclasses import dataclass

@dataclass
class Product:
    id: int
    name: str
    price: float

result = await http.get("https://api.example.com/products/1")
product = result.to(Product)
```

#### Dict

```python
result = await http.get("https://api.example.com/data")
data = result.to(dict)

print(data["field"])
```

#### List

```python
result = await http.get("https://api.example.com/users")
users = result.to(list)

for user in users:
    print(user["name"])
```

#### TypedDict

```python
from typing import TypedDict

class UserDict(TypedDict):
    id: int
    name: str
    email: str

result = await http.get("https://api.example.com/users/1")
user = result.to(UserDict)
```

### Validación de Valores Nulos

R5 valida automáticamente que los valores `None` del JSON sean compatibles con los type hints de tus dataclasses. Si un campo recibe `None` pero no está tipificado como `Optional`, se emite un `UserWarning` indicando la inconsistencia.

#### ¿Por qué es útil?

Esta validación ayuda a detectar discrepancias entre tu API y tus modelos de datos:

- ✅ **Detecta errores de tipado** tempranamente
- ✅ **No rompe el flujo** - el mapeo continúa normalmente
- ✅ **Alerta visible** - `UserWarning` en logs y consola
- ✅ **Documentación viva** - tus type hints reflejan la realidad

#### Ejemplo Básico

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Product:
    id: int
    name: str                    # No es Optional
    price: float                 # No es Optional
    description: Optional[str]   # Es Optional
    stock: Optional[int]         # Es Optional

# Caso 1: Campos opcionales con None (sin warning)
result = await http.get("https://api.example.com/products/1")
# JSON: {"id": 1, "name": "Laptop", "price": 999.99, "description": null, "stock": null}

product = result.to(Product)
# ✅ Sin warnings - description y stock son Optional

if product:
    print(f"{product.name}: ${product.price}")  # Laptop: $999.99
    print(f"Stock: {product.stock}")            # Stock: None
```

#### Ejemplo con Warning

```python
# Caso 2: Campo no-opcional con None (emite warning)
result = await http.get("https://api.example.com/products/2")
# JSON: {"id": 2, "name": null, "price": 49.99, "description": "Teclado", "stock": 5}

product = result.to(Product)
# ⚠️ UserWarning: Fields ['name'] have None values but are not typed as Optional in Product

if product:
    print(f"ID: {product.id}")      # ID: 2
    print(f"Name: {product.name}")  # Name: None (mapeado pero con warning)
    print(f"Price: {product.price}") # Price: 49.99
```

#### Ejemplo con Múltiples Campos

```python
@dataclass
class Order:
    id: int
    customer_name: str      # No Optional
    customer_email: str     # No Optional
    notes: Optional[str]    # Optional

# JSON con múltiples campos null en no-opcionales
result = await http.get("https://api.example.com/orders/1")
# JSON: {"id": 1, "customer_name": null, "customer_email": null, "notes": null}

order = result.to(Order)
# ⚠️ UserWarning: Fields ['customer_name', 'customer_email'] have None values 
#                 but are not typed as Optional in Order

# El mapeo continúa y puedes manejar el caso
if order and (order.customer_name is None or order.customer_email is None):
    print("⚠️ Orden incompleta - datos de cliente faltantes")
```

#### Comportamiento según Tipo

| Tipo Destino | Validación | Notas |
|--------------|------------|-------|
| `@dataclass` | ✅ Activa | Valida campos no-opcionales con None |
| `Pydantic BaseModel` | ⚠️ Pydantic | Pydantic ya valida con `model_validate()` |
| `dict` | ❌ Inactiva | No hay type hints que validar |
| `list` | ❌ Inactiva | No hay type hints que validar |
| `TypedDict` | ❌ Inactiva | Runtime no valida TypedDict |

#### Capturar Warnings en Tests

```python
import warnings

def test_null_validation():
    """Test que captura warnings de validación."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {
            "id": 1,
            "name": None,  # None en campo no-opcional
            "price": 99.99
        }
        
        result = Result(response=mock_response, status=200)
        product = result.to(Product)
        
        # Verificar warning
        assert len(w) == 1
        assert "not typed as Optional" in str(w[0].message)
        assert "name" in str(w[0].message)
        
        # Objeto mapeado de todas formas
        assert product is not None
        assert product.id == 1
        assert product.name is None
```

#### Mejores Prácticas

1. **Usa `Optional` correctamente**
   ```python
   @dataclass
   class User:
       id: int
       name: str
       email: Optional[str]  # Puede ser None
   ```

2. **Presta atención a los warnings**
   - Indica desajuste entre API y modelo
   - Actualiza tipos o corrige la API

3. **Documentación explícita**
   ```python
   @dataclass
   class Config:
       """Configuración de la app.
       
       Attributes:
           api_key: Requerido - nunca None
           timeout: Opcional - puede ser None
       """
       api_key: str
       timeout: Optional[int]
   ```

4. **Testing con valores None**
   ```python
   def test_handles_none_values():
       """Verifica manejo de None en campos opcionales."""
       data = {"id": 1, "name": "Test", "description": None}
       product = map_to_product(data)
       assert product.description is None  # OK porque es Optional
   ```

## Manejo de Errores

### Mapping Failure

Si `.to()` falla, retorna `None`:

```python
@inject
async def handle_mapping_error(http: Http):
    result = await http.get("https://api.example.com/data")
    
    user = result.to(User)
    
    if user is None:
        print("Failed to map to User")
        print(f"Status: {result.status}")
        print(f"Response: {result.response.text if result.response else 'None'}")
        return None
    
    return user
```

### JSON Parse Error

```python
@inject
async def handle_json_error(http: Http):
    # Response no es JSON
    result = await http.get("https://example.com/html-page")
    
    data = result.to(dict)  # None porque no puede parsear JSON
    
    if data is None:
        print("Response is not valid JSON")
        if result.response:
            print(f"Content: {result.response.text}")
```

### Type Mismatch

```python
@inject
async def handle_type_mismatch(http: Http):
    # API retorna lista pero esperamos dict
    result = await http.get("https://api.example.com/users")
    
    user = result.to(User)  # None porque response es lista, no dict
    
    if user is None:
        # Intentar como lista
        users = result.to(list)
        if users:
            print(f"Got {len(users)} users")
```

## Acceso a Response

### Response completo

```python
@inject
async def access_response(http: Http):
    result = await http.get("https://api.example.com/data")
    
    if result.response:
        print(f"Status: {result.response.status_code}")
        print(f"Headers: {result.response.headers}")
        print(f"Content: {result.response.content}")
        print(f"Text: {result.response.text}")
        print(f"JSON: {result.response.json()}")
```

### Request original

```python
@inject
async def access_request(http: Http):
    result = await http.get("https://api.example.com/data")
    
    if result.request:
        print(f"URL: {result.request.url}")
        print(f"Method: {result.request.method}")
        print(f"Headers: {result.request.headers}")
```

## Patrones Comunes

### Early Return

```python
@inject
async def early_return(http: Http):
    result = await http.get("https://api.example.com/users/1")
    
    # Return early si hay error
    if result.status != 200:
        print(f"Error: {result.status}")
        return None
    
    user = result.to(User)
    return user
```

### Fallback Value

```python
@inject
async def with_fallback(http: Http):
    result = await http.get("https://api.example.com/config")
    
    config = result.to(dict)
    
    # Usar fallback si falla
    if config is None:
        config = {"default": True}
    
    return config
```

### Retry on Specific Status

```python
@inject
async def custom_retry(http: Http):
    max_attempts = 3
    
    for attempt in range(max_attempts):
        result = await http.get("https://api.example.com/data")
        
        if result.status == 200:
            return result.to(dict)
        
        if result.status == 429:  # Rate limited
            await asyncio.sleep(2 ** attempt)
            continue
        
        # Otro error, no reintentar
        break
    
    return None
```

### Multiple Handlers

```python
@inject
async def multiple_handlers(http: Http):
    errors = []
    
    result = await http.get("https://api.example.com/data")
    
    result.on_status(404, lambda req, res: errors.append("Not found"))
          .on_status(403, lambda req, res: errors.append("Forbidden"))
          .on_status(401, lambda req, res: errors.append("Unauthorized"))
          .on_exception(lambda e: errors.append(f"Exception: {e}"))
    
    if errors:
        print(f"Errors: {errors}")
    
    return result.to(dict)
```

### Logging Helper

```python
import logging

logger = logging.getLogger(__name__)

def log_result(result: Result, operation: str):
    """Helper para logging de results."""
    if result.exception:
        logger.error(f"{operation} failed: {result.exception}")
    elif result.status >= 400:
        logger.warning(f"{operation} returned {result.status}")
    else:
        logger.info(f"{operation} succeeded: {result.status}")

@inject
async def with_logging_helper(http: Http):
    result = await http.get("https://api.example.com/users/1")
    log_result(result, "Fetch user")
    
    return result.to(User)
```

### Result Validator

```python
def validate_result(result: Result) -> bool:
    """Valida que result sea exitoso y tenga datos."""
    if result.exception:
        return False
    
    if result.status < 200 or result.status >= 300:
        return False
    
    if not result.response:
        return False
    
    try:
        result.response.json()
        return True
    except:
        return False

@inject
async def with_validator(http: Http):
    result = await http.get("https://api.example.com/data")
    
    if not validate_result(result):
        print("Invalid result")
        return None
    
    return result.to(dict)
```

## Testing

### Mock Result

```python
from unittest.mock import Mock

def test_with_mock_result():
    # Mock success
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": 1, "name": "John"}
    
    result = Result.from_response(mock_response)
    
    assert result.status == 200
    assert result.exception is None
    
    user = result.to(dict)
    assert user["name"] == "John"
```

### Mock Error

```python
def test_with_mock_error():
    error = Exception("Network error")
    result = Result.from_exception(error)
    
    assert result.status == 0
    assert result.exception == error
    assert result.response is None
```

### Test Handlers

```python
def test_result_handlers():
    mock_response = Mock()
    mock_response.status_code = 404
    
    result = Result.from_response(mock_response)
    
    called = []
    
    result.on_status(404, lambda req, res: called.append("404"))
          .on_status(200, lambda req, res: called.append("200"))
    
    assert "404" in called
    assert "200" not in called
```

## Comparación con Excepciones

### Con Excepciones (tradicional)

```python
try:
    response = await http.get("https://api.example.com/users/1")
    user = response.json()
except httpx.TimeoutException:
    print("Timeout")
except httpx.NetworkError:
    print("Network error")
except Exception as e:
    print(f"Unknown error: {e}")
```

### Con Result (R5)

```python
result = await http.get("https://api.example.com/users/1")

if result.exception:
    print(f"Error: {result.exception}")
elif result.status == 404:
    print("Not found")
elif result.status == 200:
    user = result.to(User)
```

**Beneficios de Result:**
- ✅ Flujo más claro
- ✅ Sin try/except anidados
- ✅ Fácil composición
- ✅ Type-safe
- ✅ Chaining de handlers

## Próximos Pasos

- [Overview](overview.md) - Visión general del cliente HTTP
- [Basic Usage](basic-usage.md) - Uso básico del cliente
- [Advanced](advanced.md) - Características avanzadas
- [API Reference](../../api/http.md) - Documentación completa
