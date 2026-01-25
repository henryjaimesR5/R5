from collections.abc import Callable
from typing import Any, TypeVar

from R5.ioc.container import Container, Scope


T = TypeVar("T")
C = TypeVar("C", bound=type[Any])
F = TypeVar("F", bound=Callable[..., Any])


def component(scope: Scope) -> Callable[[T], T]:
    def wrapper(func_or_cls: Any) -> Any:
        Container.registry_provider(func_or_cls, scope)
        return func_or_cls

    return wrapper


def singleton(func_or_cls: T) -> T:
    return component(scope=Scope.SINGLETON)(func_or_cls)


def factory(func_or_cls: T) -> T:
    return component(scope=Scope.FACTORY)(func_or_cls)


def resource(func_or_cls: T) -> T:
    return component(scope=Scope.RESOURCE)(func_or_cls)
