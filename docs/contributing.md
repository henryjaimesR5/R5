# Contributing

## Setup

```bash
git clone https://github.com/tu-usuario/R5.git
cd R5
uv sync
uv sync --group dev
```

## Workflow

```bash
git checkout -b feature/nueva-funcionalidad

# Tests
uv run pytest
uv run pytest --cov=R5 --cov-report=html

# Type checking y linting
uv run mypy R5/
uv run ruff check R5/
uv run ruff format R5/

# Commit (Conventional Commits)
git commit -m "feat: agregar nueva funcionalidad"
git push origin feature/nueva-funcionalidad
```

## Convenciones

- **Style**: PEP 8, type hints obligatorios, max 88 chars/línea
- **Commits**: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`
- **Tests**: Agregar tests para toda funcionalidad nueva
- **Docs**: Actualizar si los cambios afectan la API pública

## Tests

```python
import pytest
from R5.ioc import Container, singleton, inject

def test_singleton():
    Container.reset()

    @singleton
    class MyService:
        def __init__(self):
            self.value = "test"

    assert Container.resolve(MyService) is Container.resolve(MyService)

@pytest.fixture
def clean_container():
    snapshot = Container.snapshot()
    yield
    Container.restore(snapshot)
```

## Documentación

```bash
uv sync --group docs
uv run mkdocs serve    # Local
uv run mkdocs build    # Build
```

## Reportar Issues

**Bugs**: Versión de R5/Python, código para reproducir, comportamiento esperado vs actual, stack trace.

**Features**: Descripción, casos de uso, ejemplo de API propuesta.

## Licencia

Contribuciones se licencian bajo MIT.
