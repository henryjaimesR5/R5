import functools
import inspect
import logging
from collections.abc import Callable
from typing import Any

from anyio import to_thread, create_task_group, CapacityLimiter
from anyio.abc import TaskGroup

from R5.ioc import resource
from R5.ioc.container import Container

logger = logging.getLogger(__name__)


@resource
class Background:
    """Sistema de ejecución de tareas en background con anyio.
    
    Resource que gestiona:
    - TaskGroup para ejecución concurrente
    - Thread pool configurable para tareas sync
    - Inyección IoC automática en tareas
    - Manejo de errores sin propagación
    
    Uso con @inject (recomendado):
        @inject
        async def my_service(bg: Background):
            await bg.add(send_email, "user@example.com")
            await bg.add(process_payment, payment_id)
    
    Uso con context manager (control explícito de lifecycle):
        async with await Container.resolve(Background) as bg:
            await bg.add(task1)
            await bg.add(task2)
        # Cleanup automático al salir
    """
    def __init__(self, max_workers: int = 40) -> None:
        self._task_group: TaskGroup | None = None
        self._max_workers = max_workers
        self._limiter = CapacityLimiter(max_workers)
        self._ioc_cache: dict[type[Any], Any] = {}
        self._started = False
    
    async def __aenter__(self) -> 'Background':
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._started and self._task_group:
            try:
                await self._task_group.__aexit__(None, None, None)
            finally:
                self._started = False
                self._task_group = None
                self._ioc_cache.clear()
                logger.debug("Background shutdown completed")
    
    async def add(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        if not self._started:
            self._task_group = create_task_group()
            await self._task_group.__aenter__()
            self._started = True
            logger.debug(f"Background initialized with {self._max_workers} workers")
        
        wrapped_func = self._wrap_with_ioc(func)
        
        if inspect.iscoroutinefunction(wrapped_func):
            self._task_group.start_soon(
                self._safe_async_task, wrapped_func, args, kwargs
            )
        else:
            self._task_group.start_soon(
                self._safe_sync_task, wrapped_func, args, kwargs
            )
    
    async def _safe_async_task(
        self, 
        func: Callable[..., Any], 
        args: tuple[Any, ...], 
        kwargs: dict[str, Any]
    ) -> None:
        try:
            await func(*args, **kwargs)
        except Exception as e:
            logger.warning(
                f"Error in background async task {func.__name__}: {e}",
                exc_info=True
            )
    
    async def _safe_sync_task(
        self, 
        func: Callable[..., Any], 
        args: tuple[Any, ...], 
        kwargs: dict[str, Any]
    ) -> None:
        try:
            await to_thread.run_sync(
                functools.partial(func, *args, **kwargs),
                limiter=self._limiter
            )
        except Exception as e:
            logger.warning(
                f"Error in background sync task {func.__name__}: {e}",
                exc_info=True
            )
    
    def _wrap_with_ioc(self, func: Callable[..., Any]) -> Callable[..., Any]:
        sig = inspect.signature(func)
        injectable_params = {}
        
        for param_name, param in sig.parameters.items():
            if param_name in ('self', 'cls'):
                continue
            
            if param.annotation != inspect.Parameter.empty:
                if Container.in_provider(param.annotation):
                    injectable_params[param_name] = param.annotation
        
        if not injectable_params:
            return func
        
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                injected = self._resolve_dependencies(injectable_params)
                merged_kwargs = {**injected, **kwargs}
                return await func(*args, **merged_kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                injected = self._resolve_dependencies(injectable_params)
                merged_kwargs = {**injected, **kwargs}
                return func(*args, **merged_kwargs)
            return sync_wrapper
    
    def _resolve_dependencies(
        self, 
        injectable_params: dict[str, type[Any]]
    ) -> dict[str, Any]:
        resolved = {}
        
        for param_name, param_type in injectable_params.items():
            if param_type not in self._ioc_cache:
                self._ioc_cache[param_type] = Container.resolve(param_type)
            
            resolved[param_name] = self._ioc_cache[param_type]
        
        return resolved
