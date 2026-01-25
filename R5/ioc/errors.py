from typing import Type


class IoCError(Exception):
    pass


class CircularDependencyError(IoCError):
    def __init__(self, dependency_chain: list[str]):
        self.dependency_chain = dependency_chain
        chain_str = " -> ".join(dependency_chain)
        super().__init__(
            f"Circular dependency detected: {chain_str}"
        )


class ProviderNotFoundError(IoCError):
    def __init__(self, provider_type: Type, available_providers: list[str]):
        self.provider_type = provider_type
        self.available_providers = available_providers
        
        message = (
            f"Provider for type '{provider_type.__name__}' not found in container.\n"
            f"Available providers: {', '.join(available_providers) if available_providers else 'None'}\n"
            f"Did you forget to decorate {provider_type.__name__} with @singleton or @factory?"
        )
        super().__init__(message)


class AsyncProviderInSyncContextError(IoCError):
    def __init__(self, provider_type: Type):
        self.provider_type = provider_type
        super().__init__(
            f"Dependency '{provider_type.__name__}' returned an awaitable in sync context. "
            f"Make the function async or ensure the provider is sync."
        )


class DependencyInjectionError(IoCError):
    def __init__(self, provider_type: Type, param_name: str, func_name: str, original_error: Exception):
        self.provider_type = provider_type
        self.param_name = param_name
        self.func_name = func_name
        self.original_error = original_error
        
        super().__init__(
            f"Failed to inject dependency '{provider_type.__name__}' "
            f"for parameter '{param_name}' in function '{func_name}': {original_error}"
        )
