# IoC API Reference

Documentación completa de la API del módulo IoC.

## Container

::: R5.ioc.container.Container
    options:
      show_source: true
      members:
        - get_container
        - get_provider
        - in_provider
        - alias_provider
        - resolve
        - registry_provider
        - reset
        - snapshot
        - restore

## Scope

::: R5.ioc.container.Scope
    options:
      show_source: true

## Decoradores

### singleton

::: R5.ioc.providers.singleton
    options:
      show_source: true

### factory

::: R5.ioc.providers.factory
    options:
      show_source: true

### resource

::: R5.ioc.providers.resource
    options:
      show_source: true

### component

::: R5.ioc.providers.component
    options:
      show_source: true

### inject

::: R5.ioc.injection.inject
    options:
      show_source: true

### config

::: R5.ioc.configuration.config
    options:
      show_source: true

## Errores

### IoCError

::: R5.ioc.errors.IoCError
    options:
      show_source: true

### CircularDependencyError

::: R5.ioc.errors.CircularDependencyError
    options:
      show_source: true

### ProviderNotFoundError

::: R5.ioc.errors.ProviderNotFoundError
    options:
      show_source: true

### AsyncProviderInSyncContextError

::: R5.ioc.errors.AsyncProviderInSyncContextError
    options:
      show_source: true

### DependencyInjectionError

::: R5.ioc.errors.DependencyInjectionError
    options:
      show_source: true
