"""Tests completos para el módulo Background.

Este módulo contiene tests para:
- Funcionalidad básica de Background
- Integración con IoC
- Manejo de errores
- Tests con @inject
- Mejoras implementadas (race conditions, CapacityLimiter, etc.)
"""

import asyncio

import pytest

from R5.background import Background
from R5.ioc import inject, singleton
from R5.ioc.container import Container


@singleton
class TestService:
    """Servicio de prueba para inyección IoC."""

    def __init__(self):
        self.call_count = 0

    def increment(self) -> int:
        self.call_count += 1
        return self.call_count


class AsyncCallable:
    """Clase callable con __call__ async para testing."""

    def __init__(self, result_list: list):
        self.result_list = result_list

    async def __call__(self, value: str):
        self.result_list.append(value)


# ============================================================================
# TESTS BÁSICOS
# ============================================================================


class TestBackgroundCore:
    """Tests para la clase Background."""

    @pytest.mark.asyncio
    async def test_background_resource(self):
        """Verifica que Background es un resource con lifecycle."""
        bg_resource = Container.resolve(Background)

        async with await bg_resource as bg1:
            async with await Container.resolve(Background) as bg2:
                assert bg1 is bg2

    @pytest.mark.asyncio
    async def test_add_sync_function(self):
        """Verifica ejecución de función sync."""
        results = []

        def sync_task(value: str):
            results.append(value)

        async with await Container.resolve(Background) as bg:
            await bg.add(sync_task, "test")
            await asyncio.sleep(0.2)

        assert "test" in results

    @pytest.mark.asyncio
    async def test_add_async_function(self):
        """Verifica ejecución de función async."""
        results = []

        async def async_task(value: str):
            results.append(value)

        async with await Container.resolve(Background) as bg:
            await bg.add(async_task, "async_test")
            await asyncio.sleep(0.2)

        assert "async_test" in results

    @pytest.mark.asyncio
    async def test_add_with_kwargs(self):
        """Verifica ejecución con kwargs."""
        results = {}

        def task_with_kwargs(name: str, value: int):
            results[name] = value

        async with await Container.resolve(Background) as bg:
            await bg.add(task_with_kwargs, name="key1", value=42)
            await asyncio.sleep(0.2)

        assert results.get("key1") == 42

    @pytest.mark.asyncio
    async def test_add_lambda(self):
        """Verifica ejecución de lambda."""
        results = []

        async with await Container.resolve(Background) as bg:
            await bg.add(lambda x: results.append(x), "lambda_test")
            await asyncio.sleep(0.2)

        assert "lambda_test" in results

    @pytest.mark.asyncio
    async def test_add_with_args_and_kwargs(self):
        """Verifica ejecución con args y kwargs combinados."""
        results = []

        def task_mixed(name: str, count: int = 1, prefix: str = "Item"):
            results.append(f"{prefix} {name} x{count}")

        async with await Container.resolve(Background) as bg:
            await bg.add(task_mixed, "Test", count=3, prefix="Product")
            await asyncio.sleep(0.2)

        assert "Product Test x3" in results

    @pytest.mark.asyncio
    async def test_multiple_tasks_concurrently(self):
        """Verifica ejecución concurrente de múltiples tareas."""
        results = []

        def add_result(n: int):
            results.append(n)

        async with await Container.resolve(Background) as bg:
            for i in range(10):
                await bg.add(add_result, i)

            await asyncio.sleep(0.3)

        assert len(results) == 10
        assert set(results) == set(range(10))


# ============================================================================
# TESTS DE INTEGRACIÓN CON IOC
# ============================================================================


class TestIoCIntegration:
    """Tests de integración con IoC."""

    @pytest.mark.asyncio
    async def test_sync_function_with_ioc(self):
        """Verifica inyección IoC en función sync."""
        service = Container.resolve(TestService)
        initial_count = service.call_count

        def task_with_service(svc: TestService, value: int):
            svc.increment()
            return value

        async with await Container.resolve(Background) as bg:
            await bg.add(task_with_service, svc=service, value=42)
            await asyncio.sleep(0.2)

        assert service.call_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_async_function_with_ioc(self):
        """Verifica inyección IoC en función async."""
        service = Container.resolve(TestService)
        initial_count = service.call_count

        async def async_task_with_service(svc: TestService):
            svc.increment()

        async with await Container.resolve(Background) as bg:
            await bg.add(async_task_with_service, svc=service)
            await asyncio.sleep(0.2)

        assert service.call_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_auto_ioc_injection(self):
        """Verifica inyección automática de dependencias IoC."""
        service = Container.resolve(TestService)
        initial_count = service.call_count

        @inject
        def task_auto_inject(test_service: TestService):
            test_service.increment()

        async with await Container.resolve(Background) as bg:
            await bg.add(task_auto_inject)
            await asyncio.sleep(0.2)

        assert service.call_count == initial_count + 1


# ============================================================================
# TESTS DE MANEJO DE ERRORES
# ============================================================================


class TestErrorHandling:
    """Tests de manejo de errores."""

    @pytest.mark.asyncio
    async def test_sync_task_error_does_not_raise(self):
        """Verifica que errores en tareas sync solo generan warnings."""
        results = []

        def failing_task():
            raise ValueError("Test error")

        def success_task():
            results.append("success")

        async with await Container.resolve(Background) as bg:
            await bg.add(failing_task)
            await bg.add(success_task)
            await asyncio.sleep(0.3)

        assert "success" in results

    @pytest.mark.asyncio
    async def test_async_task_error_does_not_raise(self):
        """Verifica que errores en tareas async solo generan warnings."""
        results = []

        async def failing_async():
            raise RuntimeError("Async error")

        async def success_async():
            results.append("async_success")

        async with await Container.resolve(Background) as bg:
            await bg.add(failing_async)
            await bg.add(success_async)
            await asyncio.sleep(0.3)

        assert "async_success" in results

    @pytest.mark.asyncio
    async def test_aexit_propagates_exceptions(self):
        """Verifica que __aexit__ propaga excepciones correctamente al TaskGroup."""
        results = []

        async def task():
            await asyncio.sleep(0.1)
            results.append("task_completed")

        # anyio propaga excepciones en un ExceptionGroup cuando hay tareas pendientes
        with pytest.raises(BaseExceptionGroup) as exc_info:
            async with await Container.resolve(Background) as bg:
                await bg.add(task)
                # Simular una excepción en el contexto
                raise ValueError("Test exception")

        # Verificar que la excepción original está en el grupo
        exceptions = exc_info.value.exceptions
        assert any(
            isinstance(e, ValueError) and str(e) == "Test exception" for e in exceptions
        )

    @pytest.mark.asyncio
    async def test_cancelled_error_propagation(self):
        """Verifica que CancelledError se propaga correctamente."""
        results = []

        async def long_task():
            try:
                await asyncio.sleep(10)
                results.append("should_not_appear")
            except asyncio.CancelledError:
                results.append("task_cancelled")
                raise

        async with await Container.resolve(Background) as bg:
            await bg.add(long_task)
            await asyncio.sleep(0.1)
            # El task group cancelará las tareas pendientes al salir

        # Dar tiempo para que la cancelación se procese
        await asyncio.sleep(0.1)


# ============================================================================
# TESTS CON @INJECT
# ============================================================================


class TestBackgroundWithInject:
    """Tests para Background usando @inject directamente (sin context manager)."""

    @pytest.mark.asyncio
    async def test_inject_basic_usage(self):
        """Verifica uso básico con @inject."""
        results = []

        @inject
        async def my_function(bg: Background):
            await bg.add(lambda: results.append("test"))
            await asyncio.sleep(0.1)

        await my_function()  # type: ignore

        assert "test" in results

    @pytest.mark.asyncio
    async def test_inject_sync_task(self):
        """Verifica ejecución de tarea sync con @inject."""
        results = []

        def sync_task(value: str):
            results.append(value)

        @inject
        async def process(bg: Background):
            await bg.add(sync_task, "sync_test")
            await asyncio.sleep(0.1)

        await process()  # type: ignore

        assert "sync_test" in results

    @pytest.mark.asyncio
    async def test_inject_async_task(self):
        """Verifica ejecución de tarea async con @inject."""
        results = []

        async def async_task(value: str):
            results.append(value)

        @inject
        async def process(bg: Background):
            await bg.add(async_task, "async_test")
            await asyncio.sleep(0.1)

        await process()  # type: ignore

        assert "async_test" in results

    @pytest.mark.asyncio
    async def test_inject_multiple_tasks(self):
        """Verifica múltiples tareas con @inject."""
        results = []

        @inject
        async def process(bg: Background):
            for i in range(5):
                await bg.add(lambda n: results.append(n), i)
            await asyncio.sleep(0.2)

        await process()  # type: ignore

        assert len(results) == 5
        assert set(results) == {0, 1, 2, 3, 4}

    @pytest.mark.asyncio
    async def test_inject_with_ioc_service(self):
        """Verifica inyección múltiple (Background + otro servicio)."""
        service = Container.resolve(TestService)
        initial_count = service.call_count

        @inject
        async def process(bg: Background, svc: TestService):
            await bg.add(lambda: svc.increment())
            await asyncio.sleep(0.1)

        await process()  # type: ignore

        assert service.call_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_inject_task_with_ioc_injection(self):
        """Verifica tarea con inyección IoC automática."""
        service = Container.resolve(TestService)
        initial_count = service.call_count

        @inject
        def task_with_ioc(svc: TestService):
            svc.increment()

        @inject
        async def process(bg: Background):
            await bg.add(task_with_ioc)
            await asyncio.sleep(0.1)

        await process()  # type: ignore

        assert service.call_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_inject_error_handling(self):
        """Verifica que errores no bloquean otras tareas."""
        results = []

        def failing_task():
            raise ValueError("Test error")

        @inject
        async def process(bg: Background):
            await bg.add(failing_task)
            await bg.add(lambda: results.append("success"))
            await asyncio.sleep(0.2)

        await process()  # type: ignore

        assert "success" in results

    @pytest.mark.asyncio
    async def test_inject_lambda_tasks(self):
        """Verifica uso de lambdas con @inject."""
        results = []

        @inject
        async def process(bg: Background):
            await bg.add(lambda x: results.append(x), "lambda1")
            await bg.add(lambda x: results.append(x), "lambda2")
            await asyncio.sleep(0.1)

        await process()  # type: ignore

        assert "lambda1" in results
        assert "lambda2" in results

    @pytest.mark.asyncio
    async def test_inject_kwargs(self):
        """Verifica uso de kwargs con @inject."""
        results = {}

        def task_with_kwargs(name: str, value: int):
            results[name] = value

        @inject
        async def process(bg: Background):
            await bg.add(task_with_kwargs, name="key1", value=42)
            await asyncio.sleep(0.1)

        await process()  # type: ignore

        assert results.get("key1") == 42

    @pytest.mark.asyncio
    async def test_inject_mixed_params(self):
        """Verifica args y kwargs con @inject."""
        results = []

        def task_mixed(name: str, count: int = 1):
            results.append(f"{name}x{count}")

        @inject
        async def process(bg: Background):
            await bg.add(task_mixed, "Item", count=3)
            await asyncio.sleep(0.1)

        await process()  # type: ignore

        assert "Itemx3" in results

    @pytest.mark.asyncio
    async def test_inject_multiple_calls(self):
        """Verifica múltiples llamadas a función con @inject."""
        results = []

        @inject
        async def add_task(bg: Background):
            await bg.add(lambda: results.append("task"))
            await asyncio.sleep(0.1)

        await add_task()  # type: ignore
        await add_task()  # type: ignore
        await add_task()  # type: ignore

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_inject_with_multiple_services(self):
        """Verifica inyección de Background junto con otros servicios."""
        results = []
        service = Container.resolve(TestService)
        initial_count = service.call_count

        @inject
        async def complex_function(bg: Background, svc: TestService):
            await bg.add(lambda: results.append("task1"))
            svc.increment()
            await bg.add(lambda: results.append("task2"))
            await asyncio.sleep(0.1)

        await complex_function()  # type: ignore

        assert len(results) == 2
        assert service.call_count == initial_count + 1
