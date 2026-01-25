import asyncio
import pytest

from R5.background import Background
from R5.ioc import inject, singleton, Container


@singleton
class TestServiceInject:
    def __init__(self):
        self.call_count = 0
    
    def increment(self) -> int:
        self.call_count += 1
        return self.call_count


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
        service = Container.resolve(TestServiceInject)
        initial_count = service.call_count
        
        @inject
        async def process(bg: Background, svc: TestServiceInject):
            await bg.add(lambda: svc.increment())
            await asyncio.sleep(0.1)
        
        await process()  # type: ignore
        
        assert service.call_count == initial_count + 1
    
    @pytest.mark.asyncio
    async def test_inject_task_with_ioc_injection(self):
        """Verifica tarea con inyección IoC automática."""
        service = Container.resolve(TestServiceInject)
        initial_count = service.call_count
        
        def task_with_ioc(svc: TestServiceInject):
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


class TestBackgroundInjectAdvanced:
    """Tests avanzados con @inject."""
    
    @pytest.mark.asyncio
    async def test_inject_with_multiple_services(self):
        """Verifica inyección de Background junto con otros servicios."""
        results = []
        service = Container.resolve(TestServiceInject)
        initial_count = service.call_count
        
        @inject
        async def complex_function(bg: Background, svc: TestServiceInject):
            await bg.add(lambda: results.append("task1"))
            svc.increment()
            await bg.add(lambda: results.append("task2"))
            await asyncio.sleep(0.1)
        
        await complex_function()  # type: ignore
        
        assert len(results) == 2
        assert service.call_count == initial_count + 1
