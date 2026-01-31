import inspect
import warnings
from collections.abc import Callable
from contextvars import ContextVar
from enum import Enum
from typing import Any, ParamSpec, Type, TypeVar, get_type_hints

from dependency_injector import providers

from R5.ioc.errors import CircularDependencyError, ProviderNotFoundError

F = TypeVar("F", bound=Callable[..., Any])
P = ParamSpec("P")
T = TypeVar("T")


class Scope(Enum):
    SINGLETON = "singleton"
    FACTORY = "factory"
    RESOURCE = "resource"


class Container:
    _container_by_type: dict[type[Any] | Callable[..., Any], providers.Provider] = {}
    _resolution_stack: ContextVar[list[str] | None] = ContextVar(
        "_resolution_stack", default=None
    )

    @classmethod
    def get_container(cls) -> dict[type[Any] | Callable[..., Any], providers.Provider]:
        return cls._container_by_type

    @classmethod
    def get_provider(cls, provider_type: type) -> providers.Provider:
        if provider_type not in cls._container_by_type:
            available = [
                f"{t.__module__}.{t.__qualname__}"
                for t in cls._container_by_type.keys()
            ]
            raise ProviderNotFoundError(provider_type, available)
        return cls._container_by_type[provider_type]

    @classmethod
    def in_provider(cls, provider_type: type) -> bool:
        return provider_type in cls._container_by_type

    @classmethod
    def alias_provider(cls, alias: type, target: type) -> None:
        if target not in cls._container_by_type:
            available = [
                f"{t.__module__}.{t.__qualname__}"
                for t in cls._container_by_type.keys()
            ]
            raise ProviderNotFoundError(target, available)
        cls._container_by_type[alias] = cls._container_by_type[target]

    @classmethod
    def resolve(cls, dep_type: Type[T]) -> T:
        stack = cls._resolution_stack.get()
        if stack is None:
            stack = []
            cls._resolution_stack.set(stack)

        dep_name = f"{dep_type.__module__}.{dep_type.__qualname__}"

        if dep_name in stack:
            stack.append(dep_name)
            raise CircularDependencyError(stack)

        stack.append(dep_name)
        try:
            provider = cls.get_provider(dep_type)
            return provider()
        finally:
            stack.pop()
            if not stack:
                cls._resolution_stack.set(None)

    @classmethod
    def registry_provider(
        cls,
        func_or_cls: type[Any] | Callable[..., Any],
        scope: Scope,
    ) -> None:
        provider_scope = {
            Scope.SINGLETON: providers.Singleton,
            Scope.FACTORY: providers.Factory,
            Scope.RESOURCE: providers.Resource,
        }

        if func_or_cls in cls._container_by_type:
            warnings.warn(
                f"Provider for type '{func_or_cls.__name__}' is being overwritten. "
                f"This might indicate duplicate registrations.",
                UserWarning,
                stacklevel=4,
            )

        provider_class = provider_scope[scope]

        if isinstance(func_or_cls, type):
            try:
                sig = inspect.signature(func_or_cls.__init__)
                params = [
                    p
                    for p in sig.parameters.values()
                    if p.name not in ("self", "cls")
                    and p.annotation != inspect.Parameter.empty
                ]

                if params:
                    type_hints = get_type_hints(func_or_cls.__init__)
                    injectable_params = {}
                    for p in params:
                        if p.name in type_hints:
                            dep_type = type_hints[p.name]
                            if isinstance(dep_type, type) and cls.in_provider(dep_type):
                                injectable_params[p.name] = dep_type

                    if injectable_params:

                        def factory(
                            injectable_params=injectable_params, target_cls=func_or_cls
                        ):
                            kwargs = {
                                param_name: cls.resolve(dep_type)
                                for param_name, dep_type in injectable_params.items()
                            }
                            return target_cls(**kwargs)

                        provider = provider_class(factory)
                        cls._container_by_type[func_or_cls] = provider
                        return
            except Exception:
                pass

        provider = provider_class(func_or_cls)
        cls._container_by_type[func_or_cls] = provider

    @classmethod
    def reset(cls) -> None:
        cls._container_by_type.clear()
        cls._resolution_stack.set(None)

    @classmethod
    def snapshot(cls) -> dict[type[Any] | Callable[..., Any], providers.Provider]:
        return cls._container_by_type.copy()

    @classmethod
    def restore(
        cls, snapshot: dict[type[Any] | Callable[..., Any], providers.Provider]
    ) -> None:
        cls._container_by_type.clear()
        cls._container_by_type.update(snapshot)
        cls._resolution_stack.set(None)
