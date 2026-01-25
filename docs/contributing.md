# Contributing

¡Gracias por tu interés en contribuir a R5!

## Cómo Contribuir

### 1. Fork y Clone

```bash
# Fork el repositorio en GitHub
git clone https://github.com/tu-usuario/R5.git
cd R5
```

### 2. Instalar Dependencias

```bash
# Instalar uv si no lo tienes
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependencias
uv sync
uv sync --group dev
```

### 3. Crear Branch

```bash
git checkout -b feature/nueva-funcionalidad
```

### 4. Hacer Cambios

- Escribe código limpio y documentado
- Sigue las convenciones de código existentes
- Agrega tests para nuevas funcionalidades
- Actualiza la documentación si es necesario

### 5. Ejecutar Tests

```bash
# Ejecutar todos los tests
uv run pytest

# Con coverage
uv run pytest --cov=R5 --cov-report=html

# Tests específicos
uv run pytest tests/ioc/
```

### 6. Verificar Código

```bash
# Type checking
uv run mypy R5/

# Linting
uv run ruff check R5/

# Format
uv run ruff format R5/
```

### 7. Commit y Push

```bash
git add .
git commit -m "feat: agregar nueva funcionalidad"
git push origin feature/nueva-funcionalidad
```

### 8. Crear Pull Request

- Ve a GitHub y crea un Pull Request
- Describe los cambios realizados
- Referencia issues relacionados

## Convenciones de Código

### Style Guide

- Seguir PEP 8
- Usar type hints en todas las funciones
- Máximo 88 caracteres por línea (Black default)
- Docstrings en Google style

### Commits

Usar Conventional Commits:

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bugs
- `docs:` Cambios en documentación
- `test:` Agregar o modificar tests
- `refactor:` Refactorización de código
- `chore:` Tareas de mantenimiento

Ejemplos:
```
feat: add retry mechanism to HTTP client
fix: resolve circular dependency in IoC container
docs: update getting started guide
test: add tests for configuration loader
```

## Estructura del Proyecto

```
R5/
├── R5/
│   ├── ioc/          # IoC Container
│   ├── http/         # HTTP Client
│   └── background.py # Background Tasks
├── tests/            # Tests
├── docs/             # Documentación
└── examples/         # Ejemplos
```

## Tests

### Escribir Tests

```python
import pytest
from R5.ioc import Container, singleton, inject

def test_singleton_behavior():
    Container.reset()
    
    @singleton
    class MyService:
        def __init__(self):
            self.value = "test"
    
    instance1 = Container.resolve(MyService)
    instance2 = Container.resolve(MyService)
    
    assert instance1 is instance2

@pytest.mark.asyncio
async def test_async_injection():
    @inject
    async def handler(service: MyService):
        return service.value
    
    result = await handler()
    assert result == "test"
```

### Fixtures

```python
@pytest.fixture
def clean_container():
    snapshot = Container.snapshot()
    yield
    Container.restore(snapshot)
```

## Documentación

### Actualizar Docs

```bash
# Instalar dependencias de docs
uv sync --group docs

# Servir documentación localmente
uv run mkdocs serve

# Build documentación
uv run mkdocs build
```

### Escribir Docs

- Usar Markdown
- Incluir ejemplos de código
- Agregar diagramas cuando sea útil
- Mantener consistencia con docs existentes

## Reportar Issues

### Bug Reports

Incluir:
- Versión de R5
- Versión de Python
- Código para reproducir el bug
- Comportamiento esperado vs actual
- Stack trace si aplica

### Feature Requests

Incluir:
- Descripción clara de la funcionalidad
- Casos de uso
- Ejemplos de API propuesta
- Por qué es útil para el framework

## Código de Conducta

- Ser respetuoso y profesional
- Aceptar críticas constructivas
- Enfocarse en lo mejor para el proyecto
- Mostrar empatía hacia otros contribuidores

## Licencia

Al contribuir, aceptas que tus contribuciones se licencien bajo la licencia MIT.

## Preguntas

Si tienes preguntas, abre un issue o contacta a los maintainers.

¡Gracias por contribuir a R5! 🎉
