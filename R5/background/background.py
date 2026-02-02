import functools
import inspect
from collections.abc import Callable
from typing import Any

from anyio import (
    CapacityLimiter,
    Lock,
    create_task_group,
    get_cancelled_exc_class,
    to_thread,
)
from anyio.abc import TaskGroup

from R5._utils import get_logger
from R5.background.errors import BackgroundDisabledError
from R5.ioc import config, inject, resource

logger = get_logger(__name__)


@config(file="application.yml", required=False)
class _BackgroundConfig:
    background_enable: bool = True
    background_max_workers: int = 2


@resource
class Background:
    """Sistema de ejecución de tareas en background con anyio.

    Gestiona el ciclo de vida de tareas concurrentes proporcionando un TaskGroup,
    un pool de hilos para tareas síncronas e integración con inyección de dependencias.

    Attributes:
        _task_group (anyio.abc.TaskGroup): Grupo de tareas para ejecución concurrente.
        _limiter (anyio.CapacityLimiter): Limitador de capacidad para controlar concurrencia.

    Notes:
        * Soporta inyección de dependencias automática mediante `@R5/ioc`.
        * El manejo de errores está diseñado para no propagar excepciones al hilo principal.

    Examples:
        Uso con `@inject` (recomendado):

        .. code-block:: python
            @inject
            async def my_service(bg: Background):
                await bg.add(send_email, "user@example.com")
                await bg.add(process_payment, payment_id)

        Uso con context manager (control explícito de lifecycle):

        .. code-block:: python
            async with await Container.resolve(Background) as bg:
                await bg.add(task1)
                await bg.add(task2)

        Uso con inicialización directa (tradicional):

        Note:
            No se recomienda la inicialización directa fuera de entornos de prueba.
            Prefiera el uso de `@inject` para asegurar la correcta gestión de recursos.

        .. code-block:: python
            bg = Background()
            await bg.add(task1)
    """

    @inject
    def __init__(self, config: _BackgroundConfig) -> None:
        self._config = config
        self._task_group: TaskGroup | None = None
        self._max_workers = config.background_max_workers
        self._limiter = CapacityLimiter(config.background_max_workers)
        self._started = False
        self._lock = Lock()

    async def __aenter__(self) -> "Background":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._started and self._task_group:
            try:
                await self._task_group.__aexit__(exc_type, exc_val, exc_tb)
            finally:
                self._started = False
                self._task_group = None
                logger.debug("Background shutdown completed")

    async def add(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        if not self._config.background_enable:
            raise BackgroundDisabledError

        async with self._lock:
            if not self._started:
                self._task_group = create_task_group()
                await self._task_group.__aenter__()
                self._started = True
                logger.debug(f"Background initialized with {self._max_workers} workers")

            if self._task_group:
                self._task_group.start_soon(self._safe_task, func, args, kwargs)

    @staticmethod
    def _is_async_callable(func: Callable[..., Any]) -> bool:
        if isinstance(func, functools.partial):
            func = func.func

        if inspect.iscoroutinefunction(func):
            return True
        if callable(func) and hasattr(func, "__call__"):
            call_method = getattr(func, "__call__", None)
            if call_method and inspect.iscoroutinefunction(call_method):
                return True
        return False

    async def _safe_task(
        self, func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
    ):
        func_name = getattr(func, "__name__", repr(func))

        try:
            async with self._limiter:
                if self._is_async_callable(func):
                    await func(*args, **kwargs)
                else:
                    await to_thread.run_sync(functools.partial(func, *args, **kwargs))
        except get_cancelled_exc_class():
            raise
        except Exception:
            logger.exception(f"Error in background task {func_name}")
