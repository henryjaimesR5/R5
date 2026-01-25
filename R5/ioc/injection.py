import functools
import inspect
from typing import Any, TypeVar, Callable, get_type_hints, get_origin, get_args, Union

from R5.ioc.container import Container
from R5.ioc.errors import (
    AsyncProviderInSyncContextError,
    DependencyInjectionError,
)


F = TypeVar("F", bound=Callable[..., Any])


def _extract_concrete_type(annotation: Any) -> type | None:
    origin = get_origin(annotation)
    if origin is Union:
        args = get_args(annotation)
        if args:
            for arg in args:
                if arg is not type(None) and isinstance(arg, type):
                    return arg
        return None
    
    if isinstance(annotation, type):
        return annotation
    
    return None


def _inject_dependencies(
    sig: inspect.Signature,
    deps_to_inject: dict[str, type | None],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    func_name: str,
    is_async: bool,
) -> dict[str, Any]:
    bound_args = sig.bind_partial(*args, **kwargs)
    bound_args.apply_defaults()
    
    injected: dict[str, Any] = {}
    
    for param_name, dep_type in deps_to_inject.items():
        if param_name not in bound_args.arguments:
            if dep_type is None:
                injected[param_name] = None
            else:
                try:
                    provider_instance = Container.resolve(dep_type)
                    
                    if inspect.isawaitable(provider_instance):
                        if not is_async:
                            raise AsyncProviderInSyncContextError(dep_type)
                        injected[param_name] = provider_instance
                    else:
                        injected[param_name] = provider_instance
                        
                except Exception as e:
                    if isinstance(e, (AsyncProviderInSyncContextError,)):
                        raise
                    raise DependencyInjectionError(
                        dep_type, param_name, func_name, e
                    ) from e
    
    return injected


def inject(func: F) -> F:
    sig = inspect.signature(func)
    deps_to_inject: dict[str, type | None] = {}
    
    try:
        type_hints = get_type_hints(func)
    except Exception as e:
        import warnings
        warnings.warn(
            f"Could not resolve type hints for {func.__name__}: {e}. "
            f"Falling back to raw annotations. Some dependencies may not be injected.",
            UserWarning,
            stacklevel=2
        )
        type_hints = {}
        for param_name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                type_hints[param_name] = param.annotation

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        
        if param_name not in type_hints:
            continue
        
        annotation = type_hints[param_name]
        
        origin = get_origin(annotation)
        is_optional = False
        if origin is Union:
            args = get_args(annotation)
            if type(None) in args:
                is_optional = True
        
        concrete_type = _extract_concrete_type(annotation)
        
        if concrete_type is None:
            continue
        
        if Container.in_provider(concrete_type):
            deps_to_inject[param_name] = concrete_type
        elif is_optional:
            deps_to_inject[param_name] = None
    
    new_params = []
    found_first_injectable = False
    
    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            new_params.append(param)
            continue
        
        if param_name in deps_to_inject:
            found_first_injectable = True
        
        if found_first_injectable and param_name not in deps_to_inject:
            if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                new_param = param.replace(kind=inspect.Parameter.KEYWORD_ONLY)
                new_params.append(new_param)
            else:
                new_params.append(param)
        else:
            new_params.append(param)
    
    new_sig = sig.replace(parameters=new_params)

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            injected = _inject_dependencies(
                sig, deps_to_inject, args, kwargs, func.__name__, is_async=True
            )
            
            for param_name, provider_instance in injected.items():
                if inspect.isawaitable(provider_instance):
                    kwargs[param_name] = await provider_instance
                else:
                    kwargs[param_name] = provider_instance

            return await func(*args, **kwargs)

        async_wrapper.__signature__ = new_sig  # type: ignore
        return async_wrapper  # type: ignore
    else:

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            injected = _inject_dependencies(
                sig, deps_to_inject, args, kwargs, func.__name__, is_async=False
            )
            kwargs.update(injected)
            return func(*args, **kwargs)

        sync_wrapper.__signature__ = new_sig  # type: ignore
        return sync_wrapper  # type: ignore
