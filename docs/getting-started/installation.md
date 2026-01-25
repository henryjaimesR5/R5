# Instalación

Esta guía te muestra cómo instalar R5 en tu proyecto.

## Requisitos

- Python 3.14 o superior
- `pip` o `uv` como gestor de paquetes

## Instalación con pip

```bash
pip install r5
```

## Instalación con uv (Recomendado)

[uv](https://github.com/astral-sh/uv) es un gestor de paquetes ultra rápido para Python.

```bash
# Instalar uv si no lo tienes
curl -LsSf https://astral.sh/uv/install.sh | sh

# Agregar R5 a tu proyecto
uv add r5
```

## Instalación desde el código fuente

```bash
git clone https://github.com/grupor5/R5.git
cd R5
uv sync
```

## Dependencias

R5 instala automáticamente las siguientes dependencias:

- **anyio** (>=4.12.0) - Para tareas concurrentes
- **dependency-injector** (>=4.48.3) - Motor de IoC
- **httpx** (>=0.28.1) - Cliente HTTP asíncrono
- **pydantic** (>=2.12.5) - Validación de datos
- **pydantic-settings** (>=2.12.0) - Gestión de configuración
- **pyyaml** (>=6.0.3) - Soporte para archivos YAML

## Verificar la instalación

Verifica que R5 se instaló correctamente:

```python
import R5
from R5.ioc import singleton, inject
from R5.http import Http
from R5.background import Background

print("✅ R5 instalado correctamente")
```

## Dependencias opcionales

### Para desarrollo

```bash
uv add --dev pytest pytest-asyncio pytest-cov
```

### Para documentación

```bash
uv add --group docs mkdocs mkdocs-material mkdocstrings[python]
```

## Actualizar R5

### Con pip

```bash
pip install --upgrade r5
```

### Con uv

```bash
uv add --upgrade r5
```

## Desinstalación

### Con pip

```bash
pip uninstall r5
```

### Con uv

```bash
uv remove r5
```

## Próximos pasos

Una vez instalado R5, continúa con:

- [Quick Start](quickstart.md) - Tu primera aplicación con R5
- [Core Concepts](core-concepts.md) - Conceptos fundamentales del framework
