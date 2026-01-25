# Changelog

Todos los cambios notables en R5 serán documentados aquí.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Documentación completa con MkDocs y mkdocstrings
- Ejemplos de uso básicos y avanzados
- Guías para IoC, HTTP y Background
- Patrones de diseño comunes

## [0.1.0] - 2025-01-25

### Added
- IoC Container con inyección de dependencias automática
  - Decoradores `@singleton`, `@factory`, `@resource`
  - Decorador `@inject` para inyección automática
  - Decorador `@config` para configuración multi-formato
  - Soporte para .env, JSON, YAML, Properties
  - Detección de dependencias circulares
  - Type-safe dependency resolution

- Cliente HTTP asíncrono
  - Connection pooling con httpx
  - Result pattern para manejo de errores
  - Retry automático configurable
  - Handlers (before/after)
  - Proxy rotation
  - Mapeo automático a DTOs (Pydantic, dataclasses)
  - Configuración flexible de timeouts

- Sistema de Background Tasks
  - Ejecución concurrente con anyio
  - Thread pool para tareas síncronas
  - Inyección IoC en tareas
  - Error handling robusto
  - Lifecycle management automático

### Technical
- Python 3.14+ requerido
- Dependencias principales:
  - anyio >= 4.12.0
  - dependency-injector >= 4.48.3
  - httpx >= 0.28.1
  - pydantic >= 2.12.5
  - pyyaml >= 6.0.3

## [0.0.1] - 2025-01-01

### Added
- Initial project setup
- Basic project structure

---

## Tipos de Cambios

- `Added` - Nuevas funcionalidades
- `Changed` - Cambios en funcionalidades existentes
- `Deprecated` - Funcionalidades que serán removidas
- `Removed` - Funcionalidades removidas
- `Fixed` - Corrección de bugs
- `Security` - Correcciones de seguridad

[Unreleased]: https://github.com/grupor5/R5/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/grupor5/R5/releases/tag/v0.1.0
[0.0.1]: https://github.com/grupor5/R5/releases/tag/v0.0.1
