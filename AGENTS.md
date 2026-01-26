# AGENTS.md - R5 Framework

**Especificación y Guía de Desarrollo para Agentes de IA y Desarrolladores**

Este documento define las convenciones, workflows y mejores prácticas para trabajar en el proyecto R5. Es especialmente útil para agentes de IA (como Cascade, Copilot, etc.) pero también sirve como referencia para desarrolladores humanos.

---

## 📋 Tabla de Contenidos

- [Información General](#información-general)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Herramientas y Comandos](#herramientas-y-comandos)
- [Convenciones de Código](#convenciones-de-código)
- [Workflow de Desarrollo](#workflow-de-desarrollo)
- [Convenciones de Commits](#convenciones-de-commits)
- [Testing](#testing)
- [Documentación](#documentación)
- [Proceso Completo por Feature](#proceso-completo-por-feature)
- [Checklist de Calidad](#checklist-de-calidad)

---

## 📦 Información General

### Stack Tecnológico

- **Lenguaje**: Python 3.14+
- **Gestor de Paquetes**: `uv` (recomendado)
- **Framework Base**: asyncio, anyio
- **HTTP Client**: httpx
- **IoC**: dependency-injector
- **Validación**: pydantic
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Documentación**: mkdocs, mkdocs-material, mkdocstrings
- **Linting**: ruff, mypy

### Principios del Framework

1. **Simplicidad**: API clara y directa, sin magia excesiva
2. **Type-Safety**: Aprovechar el sistema de tipos de Python
3. **Performance**: Operaciones asíncronas por defecto
4. **Modularidad**: Componentes independientes y reutilizables
5. **Developer Experience**: Fácil de usar y de entender

---

## 🗂️ Estructura del Proyecto

```
R5/
├── R5/                          # Código fuente del framework
│   ├── ioc/                     # IoC Container
│   │   ├── __init__.py
│   │   ├── container.py         # Contenedor principal
│   │   ├── providers.py         # Providers (singleton, factory, resource)
│   │   ├── injection.py         # Decorador @inject
│   │   └── configuration.py     # Decorador @config
│   ├── http/                    # HTTP Client
│   │   ├── __init__.py
│   │   ├── http.py             # Cliente HTTP principal
│   │   ├── result.py           # Result pattern
│   │   └── errors.py           # Excepciones HTTP
│   ├── __init__.py
│   └── background.py           # Background tasks con anyio
├── tests/                      # Tests del framework
│   ├── ioc/                    # Tests IoC
│   ├── http/                   # Tests HTTP
│   ├── background/             # Tests Background
│   └── conftest.py             # Fixtures compartidas
├── docs/                       # Documentación (MkDocs)
│   ├── api/                    # Referencia de API
│   ├── guides/                 # Guías detalladas
│   ├── examples/               # Ejemplos completos
│   └── getting-started/        # Quick start
├── scripts/                    # Scripts de utilidad
│   ├── build_docs.sh
│   └── serve_docs.sh
├── site/                       # Documentación generada (gitignored)
├── examples.py                 # Ejemplos ejecutables
├── Makefile                    # Comandos make
├── pyproject.toml              # Configuración del proyecto
├── pytest.ini                  # Configuración pytest
├── mkdocs.yml                  # Configuración MkDocs
└── AGENTS.md                   # Este archivo
```

### Componentes Principales

#### IoC Container (`R5/ioc/`)
- **Container**: Gestión de dependencias y resolución
- **Providers**: Singleton, Factory, Resource
- **Injection**: Inyección automática basada en type hints
- **Configuration**: Carga de configuración desde archivos

#### HTTP Client (`R5/http/`)
- **Http**: Cliente HTTP asíncrono con pooling
- **Result**: Pattern para manejo de errores
- **Retry**: Mecanismo de reintentos configurable

#### Background Tasks (`R5/background.py`)
- **Background**: Ejecución concurrente con anyio
- Soporte para funciones sync y async
- Inyección IoC en tareas

---

## 🛠️ Herramientas y Comandos

### Gestor de Paquetes: `uv`

**IMPORTANTE**: Todos los comandos deben ejecutarse con `uv`:

```bash
# ✅ CORRECTO
uv run pytest
uv run python examples.py
uv run mkdocs serve

# ❌ INCORRECTO
pytest
python examples.py
mkdocs serve
```

### Makefile Targets

El proyecto incluye un `Makefile` con comandos útiles:

| Comando | Descripción |
|---------|-------------|
| `make install` | Instalar dependencias de producción |
| `make dev` | Instalar dependencias de desarrollo |
| `make docs-deps` | Instalar dependencias de documentación |
| `make test` | Ejecutar todos los tests |
| `make test-cov` | Tests con reporte de cobertura |
| `make test-watch` | Tests en modo watch |
| `make lint` | Ejecutar linters (ruff, mypy) |
| `make format` | Formatear código con ruff |
| `make docs` | Construir documentación |
| `make docs-serve` | Servir documentación localmente (port 8000) |
| `make docs-deploy` | Desplegar docs a GitHub Pages |
| `make clean` | Limpiar archivos generados |
| `make build` | Construir paquete |
| `make examples` | Ejecutar scripts de ejemplo |
| `make check` | Lint + test en un solo comando |
| `make all` | Setup completo (install + dev + docs + test) |

### Comandos Directos con `uv`

```bash
# Instalar dependencias
uv sync
uv sync --group dev
uv sync --group docs

# Tests
uv run pytest                           # Todos los tests
uv run pytest tests/ioc/                # Solo tests IoC
uv run pytest tests/http/               # Solo tests HTTP
uv run pytest tests/background/         # Solo tests Background
uv run pytest -v                        # Verbose
uv run pytest -k "test_singleton"       # Test específico
uv run pytest --cov=R5 --cov-report=html  # Con coverage

# Linting y Format
uv run ruff check R5/                   # Verificar estilo
uv run ruff format R5/                  # Formatear código
uv run ruff check --fix R5/             # Auto-fix errores
uv run mypy R5/                         # Type checking

# Documentación
uv run mkdocs serve                     # Servir docs en localhost:8000
uv run mkdocs build                     # Construir docs
uv run mkdocs gh-deploy                 # Desplegar a GitHub Pages

# Ejemplos
uv run python examples.py
```

---

## 💻 Convenciones de Código

### Style Guide

1. **PEP 8**: Seguir estándar de código Python
2. **Line Length**: Máximo 88 caracteres (Black default)
3. **Type Hints**: Obligatorios en todas las funciones públicas
4. **Docstrings**: Estilo Google para funciones públicas
5. **Imports**: Organizados (stdlib → third-party → local)
6. **Async First**: Preferir funciones async cuando sea posible

### Ejemplo de Código Bien Formateado

```python
from typing import Optional
import asyncio

from httpx import AsyncClient
from pydantic import BaseModel

from R5.ioc import singleton, inject


@singleton
class UserService:
    """Service for managing user operations.
    
    This service handles user-related business logic and data access.
    """
    
    def __init__(self) -> None:
        self.users: dict[int, str] = {}
    
    def get_user(self, user_id: int) -> Optional[str]:
        """Get user by ID.
        
        Args:
            user_id: The user identifier
            
        Returns:
            User name if found, None otherwise
        """
        return self.users.get(user_id)
    
    async def fetch_user(self, user_id: int) -> Optional[str]:
        """Fetch user asynchronously.
        
        Args:
            user_id: The user identifier
            
        Returns:
            User name if found, None otherwise
        """
        await asyncio.sleep(0.1)  # Simulate async operation
        return self.get_user(user_id)
```

### Type Hints Obligatorios

```python
# ✅ CORRECTO
def process_data(items: list[str], count: int) -> dict[str, int]:
    return {item: count for item in items}

async def fetch_user(user_id: int) -> Optional[User]:
    result = await http.get(f"/users/{user_id}")
    return result.to(User)

# ❌ INCORRECTO
def process_data(items, count):  # Sin type hints
    return {item: count for item in items}

async def fetch_user(user_id):  # Sin type hints
    result = await http.get(f"/users/{user_id}")
    return result.to(User)
```

### Imports Organization

```python
# 1. Standard library
import asyncio
from typing import Optional, Dict, List
from dataclasses import dataclass

# 2. Third-party
import httpx
from pydantic import BaseModel

# 3. Local imports
from R5.ioc import singleton, inject
from R5.http import Http
from R5.background import Background
```

### Naming Conventions

- **Classes**: `PascalCase` (ej. `UserService`, `HttpClient`)
- **Functions/Methods**: `snake_case` (ej. `get_user`, `fetch_data`)
- **Constants**: `UPPER_SNAKE_CASE` (ej. `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private**: Prefijo `_` (ej. `_internal_method`)
- **Variables**: `snake_case` (ej. `user_id`, `response_data`)

---

## 🔄 Workflow de Desarrollo

### 1. Setup Inicial

```bash
# Clonar repositorio
git clone https://github.com/grupor5/R5.git
cd R5

# Instalar todas las dependencias
make install
make dev
make docs-deps

# O usando uv directamente
uv sync --group dev --group docs

# Verificar instalación
make test
```

### 2. Crear Branch

```bash
# Feature branch
git checkout -b feature/nueva-funcionalidad

# Bug fix branch
git checkout -b fix/corregir-bug

# Documentation branch
git checkout -b docs/actualizar-guias
```

### 3. Desarrollo

1. **Escribir código** siguiendo convenciones
2. **Type hints** en todas las funciones
3. **Docstrings** para APIs públicas
4. **Manejo de errores** apropiado

### 4. Verificación Local

```bash
# Formatear código
make format

# Verificar estilo
make lint

# Ejecutar tests
make test

# Todo junto
make check
```

---

## 📝 Convenciones de Commits

### Conventional Commits

Seguir el estándar [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Descripción | Ejemplo |
|------|-------------|---------|
| `feat` | Nueva funcionalidad | `feat(http): add retry mechanism` |
| `fix` | Corrección de bug | `fix(ioc): resolve circular dependency` |
| `docs` | Cambios en documentación | `docs(readme): update installation guide` |
| `test` | Agregar/modificar tests | `test(http): add integration tests` |
| `refactor` | Refactorización sin cambios funcionales | `refactor(ioc): simplify container logic` |
| `perf` | Mejora de rendimiento | `perf(http): optimize connection pooling` |
| `style` | Cambios de formato | `style: fix code formatting` |
| `chore` | Tareas de mantenimiento | `chore: update dependencies` |
| `ci` | Cambios en CI/CD | `ci: add GitHub Actions workflow` |
| `build` | Cambios en build system | `build: update pyproject.toml` |

### Scopes

| Scope | Descripción |
|-------|-------------|
| `ioc` | IoC Container |
| `http` | HTTP Client |
| `background` | Background Tasks |
| `docs` | Documentación |
| `tests` | Tests |
| `deps` | Dependencias |

### Ejemplos de Commits

```bash
# Feature nueva
git commit -m "feat(http): add automatic retry with exponential backoff"

# Bug fix
git commit -m "fix(ioc): prevent circular dependency detection false positives"

# Documentación
git commit -m "docs(guides): add HTTP client advanced usage examples"

# Test
git commit -m "test(background): add tests for concurrent task execution"

# Refactor
git commit -m "refactor(ioc): extract provider logic into separate classes"

# Performance
git commit -m "perf(http): reduce memory allocation in result mapping"

# Chore
git commit -m "chore(deps): update httpx to 0.28.1"

# Multiple scopes
git commit -m "feat(ioc,http): integrate IoC injection in HTTP client"
```

### Commit Body (Opcional)

Para cambios complejos, agregar detalles:

```bash
git commit -m "feat(http): add retry mechanism with exponential backoff

- Add RetryConfig dataclass for retry configuration
- Implement exponential backoff algorithm
- Support custom retry predicates
- Add tests for retry scenarios

Closes #42"
```

### Commits Atomicos

Cada commit debe ser atómico y funcional:

```bash
# ✅ CORRECTO - Commits separados por funcionalidad
git commit -m "feat(http): add retry configuration"
git commit -m "test(http): add retry tests"
git commit -m "docs(http): document retry feature"

# ❌ INCORRECTO - Todo en un commit
git commit -m "add retry feature with tests and docs"
```

---

## 🧪 Testing

### Principios de Testing

1. **Coverage**: Mínimo 80% de cobertura
2. **Isolation**: Tests independientes entre sí
3. **Clarity**: Nombres descriptivos de tests
4. **Speed**: Tests rápidos (< 1s por test)
5. **Assertions**: Claras y específicas

### Estructura de Tests

```python
import pytest
from R5.ioc import Container, singleton, inject


class TestSingleton:
    """Tests for singleton provider."""
    
    @pytest.fixture(autouse=True)
    def reset_container(self):
        """Reset container before each test."""
        Container.reset()
        yield
        Container.reset()
    
    def test_singleton_returns_same_instance(self):
        """Singleton should return the same instance on multiple resolves."""
        @singleton
        class Service:
            pass
        
        instance1 = Container.resolve(Service)
        instance2 = Container.resolve(Service)
        
        assert instance1 is instance2
    
    def test_singleton_with_dependencies(self):
        """Singleton should inject dependencies correctly."""
        @singleton
        class Database:
            pass
        
        @singleton
        class Service:
            def __init__(self, db: Database):
                self.db = db
        
        service = Container.resolve(Service)
        assert isinstance(service.db, Database)
```

### Naming Convention

```python
# Pattern: test_<component>_<scenario>_<expected_result>

def test_container_resolve_singleton_returns_same_instance():
    pass

def test_http_get_with_retry_succeeds_after_failures():
    pass

def test_background_add_task_executes_async_function():
    pass

# ✅ CORRECTO - Descriptivo
def test_inject_decorator_resolves_dependencies_from_type_hints():
    pass

# ❌ INCORRECTO - Vago
def test_inject():
    pass
```

### Markers de Pytest

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    pass

@pytest.mark.slow
def test_long_running_operation():
    """Test that takes more than 1 second."""
    pass

@pytest.mark.integration
async def test_http_integration():
    """Integration test with real HTTP calls."""
    pass

@pytest.mark.parametrize("value,expected", [
    (1, "one"),
    (2, "two"),
    (3, "three"),
])
def test_with_parameters(value, expected):
    """Test with multiple parameter sets."""
    pass
```

### Fixtures

```python
# tests/conftest.py
import pytest
from R5.ioc import Container

@pytest.fixture
def clean_container():
    """Provide clean IoC container."""
    Container.reset()
    yield Container
    Container.reset()

@pytest.fixture
async def http_client():
    """Provide HTTP client for testing."""
    from R5.http import Http
    async with Http() as client:
        yield client
```

### Ejecutar Tests

```bash
# Todos los tests
make test
uv run pytest

# Con coverage
make test-cov
uv run pytest --cov=R5 --cov-report=html --cov-report=term

# Tests específicos
uv run pytest tests/ioc/
uv run pytest tests/http/test_http.py
uv run pytest tests/http/test_http.py::test_get_success

# Verbose
uv run pytest -v

# Con output de print
uv run pytest -s

# Tests por marker
uv run pytest -m asyncio
uv run pytest -m "not slow"

# Watch mode
make test-watch
uv run pytest-watch
```

---

## 📚 Documentación

### Estructura de Documentación

```
docs/
├── index.md                    # Landing page
├── getting-started/
│   ├── installation.md        # Instalación
│   ├── quickstart.md          # Quick start
│   └── core-concepts.md       # Conceptos básicos
├── guides/
│   ├── ioc/
│   │   ├── overview.md        # Visión general IoC
│   │   ├── providers.md       # Providers
│   │   ├── injection.md       # Inyección
│   │   └── configuration.md   # Configuración
│   ├── http/
│   │   ├── overview.md        # Visión general HTTP
│   │   ├── client.md          # Cliente HTTP
│   │   ├── result.md          # Result pattern
│   │   └── retry.md           # Retry mechanism
│   └── background/
│       ├── overview.md        # Visión general
│       └── tasks.md           # Task management
├── examples/
│   ├── simple.md              # Ejemplos simples
│   ├── patterns.md            # Patrones comunes
│   └── real-world.md          # Casos reales
├── api/
│   ├── ioc.md                 # API Reference IoC
│   ├── http.md                # API Reference HTTP
│   └── background.md          # API Reference Background
├── contributing.md             # Guía de contribución
└── changelog.md                # Changelog
```

### Escribir Documentación

#### Format Markdown

```markdown
# Título Principal

Introducción breve del tema.

## Sección

Contenido de la sección.

### Subsección

Detalles específicos.

#### Código de Ejemplo

```python
from R5.ioc import inject

@inject
async def handler(service: MyService):
    return await service.process()
```

#### Notas Importantes

!!! note
    Información adicional relevante.

!!! warning
    Advertencia importante.

!!! tip
    Consejo útil.
```

#### Docstrings

Usar formato Google:

```python
def process_data(items: list[str], max_count: int = 100) -> dict[str, int]:
    """Process list of items and return count mapping.
    
    This function processes a list of string items and creates
    a mapping of each item to its occurrence count, limited by max_count.
    
    Args:
        items: List of string items to process
        max_count: Maximum count per item (default: 100)
        
    Returns:
        Dictionary mapping items to their counts
        
    Raises:
        ValueError: If items list is empty
        
    Example:
        >>> process_data(["a", "b", "a"], max_count=10)
        {"a": 2, "b": 1}
    """
    if not items:
        raise ValueError("Items list cannot be empty")
    
    counts = {}
    for item in items:
        counts[item] = min(counts.get(item, 0) + 1, max_count)
    
    return counts
```

### Generar Documentación

```bash
# Instalar dependencias
make docs-deps
uv sync --group docs

# Servir localmente (http://127.0.0.1:8000)
make docs-serve
uv run mkdocs serve

# Build estático
make docs
uv run mkdocs build

# Desplegar a GitHub Pages
make docs-deploy
uv run mkdocs gh-deploy
```

### Configuración MkDocs

El archivo `mkdocs.yml` define la estructura:

```yaml
site_name: R5 Framework
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - toc.integrate
    - search.suggest

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: google
```

---

## 🚀 Proceso Completo por Feature

Este es el workflow completo para desarrollar una nueva funcionalidad:

### Fase 1: Planificación

1. **Crear Issue** (opcional pero recomendado)
   - Describir la funcionalidad
   - Definir casos de uso
   - Especificar API propuesta

2. **Crear Branch**
   ```bash
   git checkout -b feature/nombre-descriptivo
   ```

### Fase 2: Desarrollo

3. **Implementar Código**
   - Escribir código en `R5/`
   - Seguir convenciones de estilo
   - Agregar type hints
   - Agregar docstrings
   
4. **Formatear y Lint**
   ```bash
   make format
   make lint
   ```

### Fase 3: Testing

5. **Escribir Tests**
   - Crear archivo en `tests/`
   - Tests unitarios
   - Tests de integración (si aplica)
   - Mínimo 80% coverage
   
6. **Ejecutar Tests**
   ```bash
   make test-cov
   ```
   
7. **Verificar Coverage**
   - Abrir `htmlcov/index.html`
   - Asegurar cobertura adecuada

### Fase 4: Ejemplos

8. **Crear Ejemplo**
   - Agregar ejemplo en `examples.py` o crear nuevo archivo
   - Ejemplo simple y claro
   - Comentado adecuadamente
   
9. **Probar Ejemplo**
   ```bash
   uv run python examples.py
   ```

### Fase 5: Documentación

10. **Documentar API**
    - Agregar/actualizar `docs/api/`
    - Docstrings completos
    
11. **Actualizar Guías**
    - Crear/actualizar guía en `docs/guides/`
    - Explicar casos de uso
    - Incluir ejemplos
    
12. **Actualizar README** (si aplica)
    - Agregar feature en lista
    - Actualizar ejemplos si es relevante

13. **Build y Verificar Docs**
    ```bash
    make docs-serve
    # Verificar en http://127.0.0.1:8000
    ```

### Fase 6: Verificación Final

14. **Checklist Completo**
    - [ ] Código implementado y formateado
    - [ ] Type hints completos
    - [ ] Docstrings agregados
    - [ ] Tests escritos (>80% coverage)
    - [ ] Todos los tests pasan
    - [ ] Lint sin errores
    - [ ] Ejemplo funcional
    - [ ] Documentación actualizada
    - [ ] README actualizado (si aplica)

15. **Commit Changes**
    ```bash
    git add .
    git commit -m "feat(scope): descripción clara"
    ```

### Fase 7: Pull Request

16. **Push y PR**
    ```bash
    git push origin feature/nombre-descriptivo
    ```
    
17. **Crear Pull Request**
    - Título descriptivo
    - Descripción detallada
    - Referenciar issues
    - Screenshots/ejemplos si aplica

---

## ✅ Checklist de Calidad

Usar este checklist antes de cada commit/PR:

### Código

- [ ] Código sigue convenciones de estilo (PEP 8)
- [ ] Type hints en todas las funciones públicas
- [ ] Docstrings con formato Google
- [ ] Sin código comentado innecesario
- [ ] Sin imports no utilizados
- [ ] Sin variables no utilizadas
- [ ] Manejo apropiado de errores

### Tests

- [ ] Tests unitarios escritos
- [ ] Tests de integración (si aplica)
- [ ] Coverage > 80%
- [ ] Todos los tests pasan
- [ ] Tests son independientes
- [ ] Nombres de tests descriptivos

### Documentación

- [ ] API documentada en `docs/api/`
- [ ] Guía actualizada en `docs/guides/`
- [ ] Ejemplo funcional creado
- [ ] README actualizado (si aplica)
- [ ] CHANGELOG actualizado (si aplica)

### Verificación

- [ ] `make format` ejecutado
- [ ] `make lint` sin errores
- [ ] `make test` todos pasan
- [ ] `make docs-serve` funciona
- [ ] Ejemplos se ejecutan sin errores

### Git

- [ ] Commits atómicos
- [ ] Mensajes siguen Conventional Commits
- [ ] Branch con nombre descriptivo
- [ ] Sin archivos generados en git (.pyc, __pycache__, etc.)

---

## 🎯 Tips para Agentes de IA

### Cuando Implementar Nueva Funcionalidad

1. **Leer contexto**: Revisar archivos relacionados antes de implementar
2. **Seguir patrones**: Usar patrones existentes en el código
3. **Tests primero**: Considerar TDD cuando sea apropiado
4. **Commits granulares**: Hacer commits pequeños y frecuentes
5. **Documentar inline**: Agregar docstrings mientras codificas

### Cuando Hacer Refactor

1. **Tests primero**: Asegurar que existen tests antes de refactorizar
2. **Pequeños pasos**: Refactorizar incrementalmente
3. **Verificar tests**: Ejecutar tests después de cada cambio
4. **Mantener API**: No romper APIs públicas sin deprecation

### Cuando Corregir Bugs

1. **Reproducir**: Crear test que reproduzca el bug
2. **Fix mínimo**: Hacer el cambio mínimo necesario
3. **Verificar**: Asegurar que el test pasa
4. **Regression**: Considerar tests adicionales

### Comandos más Usados

```bash
# Setup
make install && make dev

# Desarrollo diario
make format          # Antes de commit
make lint           # Verificar estilo
make test           # Verificar tests
make check          # Todo junto

# Documentación
make docs-serve     # Ver docs localmente

# Ejemplos
uv run python examples.py
```

---

## 📖 Referencias

- **Repositorio**: https://github.com/grupor5/R5
- **Documentación**: https://r5.dev (cuando esté disponible)
- **Conventional Commits**: https://www.conventionalcommits.org/
- **PEP 8**: https://pep8.org/
- **Google Docstrings**: https://google.github.io/styleguide/pyguide.html
- **MkDocs**: https://www.mkdocs.org/
- **pytest**: https://docs.pytest.org/

---

## 🤝 Soporte

- **Issues**: https://github.com/grupor5/R5/issues
- **Discussions**: https://github.com/grupor5/R5/discussions
- **Email**: support@r5.dev

---

**Última actualización**: 2026-01-26

**Versión**: 1.0.0
