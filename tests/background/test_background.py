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


class TestIntegration:
    """Tests de integración completos."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test completo de workflow con Background."""
        results = []
        
        def sync_task(msg: str):
            results.append(f"sync: {msg}")
        
        async def async_task(msg: str):
            results.append(f"async: {msg}")
        
        async with await Container.resolve(Background) as bg:
            await bg.add(sync_task, "manual")
            await bg.add(async_task, "manual_async")
            await asyncio.sleep(0.3)
        
        assert "sync: manual" in results
        assert "async: manual_async" in results
    
    @pytest.mark.asyncio
    async def test_mixed_sync_async_tasks(self):
        """Verifica mezcla de tareas sync y async."""
        results = []
        
        def sync_1():
            results.append("sync_1")
        
        async def async_1():
            results.append("async_1")
        
        def sync_2():
            results.append("sync_2")
        
        async def async_2():
            results.append("async_2")
        
        async with await Container.resolve(Background) as bg:
            await bg.add(sync_1)
            await bg.add(async_1)
            await bg.add(sync_2)
            await bg.add(async_2)
            await asyncio.sleep(0.3)
        
        assert len(results) == 4
        assert "sync_1" in results
        assert "async_1" in results
        assert "sync_2" in results
        assert "async_2" in results
    
