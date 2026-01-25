import inspect
import pytest
from typing import Optional
from R5.ioc import singleton, factory, inject


class TestBasicInjection:
    def test_inject_single_dependency(self):
        @singleton
        class MyService:
            def __init__(self):
                self.value = "test_service"
        
        @inject
        def handler(service: MyService):
            return service.value
        
        result = handler() # type: ignore
        assert result == "test_service"
    
    def test_inject_multiple_dependencies(self):
        @singleton
        class ServiceA:
            def __init__(self):
                self.value = "A"
        
        @singleton
        class ServiceB:
            def __init__(self):
                self.value = "B"
        
        @inject
        def handler(service_a: ServiceA, service_b: ServiceB):
            return f"{service_a.value}+{service_b.value}"
        
        result = handler() # type: ignore
        assert result == "A+B"
    
    def test_inject_with_manual_args(self):
        @singleton
        class MyService:
            def __init__(self):
                self.value = "injected"
        
        @inject
        def handler(manual_arg: str, service: MyService):
            return f"{manual_arg}:{service.value}"
        
        result = handler(manual_arg="manual") # type: ignore
        assert result == "manual:injected"
    
    def test_inject_preserves_function_metadata(self):
        @singleton
        class MyService:
            pass
        
        @inject
        def my_function(service: MyService):
            """This is my function"""
            return service
        
        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "This is my function"


class TestAsyncInjection:
    @pytest.mark.asyncio
    async def test_inject_async_function(self):
        @singleton
        class MyService:
            def __init__(self):
                self.value = "async_test"
        
        @inject
        async def async_handler(service: MyService):
            return service.value
        
        result = await async_handler() # type: ignore
        assert result == "async_test"
    
    @pytest.mark.asyncio
    async def test_inject_multiple_async(self):
        @singleton
        class ServiceA:
            def __init__(self):
                self.value = "A"
        
        @factory
        class ServiceB:
            def __init__(self):
                self.value = "B"
        
        @inject
        async def async_handler(service_a: ServiceA, service_b: ServiceB):
            return f"{service_a.value}+{service_b.value}"
        
        result = await async_handler() # type: ignore
        assert result == "A+B"


class TestOptionalInjection:
    def test_inject_optional_registered(self):
        @singleton
        class MyService:
            def __init__(self):
                self.value = "present"
        
        @inject
        def handler(service: Optional[MyService]):
            return service.value if service else "none"
        
        result = handler() # type: ignore
        assert result == "present"
    
    def test_inject_optional_not_registered(self):
        class UnregisteredService:
            pass
        
        @inject
        def handler(service: Optional[UnregisteredService]):
            return "none" if service is None else "present"
        
        result = handler() # type: ignore
        assert result == "none"


class TestSingletonBehavior:
    def test_singleton_returns_same_instance(self):
        @singleton
        class MyService:
            def __init__(self):
                self.counter = 0
        
        @inject
        def handler1(service: MyService):
            service.counter += 1
            return service
        
        @inject
        def handler2(service: MyService):
            return service
        
        instance1 = handler1() # type: ignore
        instance2 = handler2() # type: ignore
        
        assert instance1 is instance2
        assert instance2.counter == 1


class TestFactoryBehavior:
    def test_factory_returns_different_instances(self):
        @factory
        class MyFactory:
            def __init__(self):
                self.value = "factory"
        
        @inject
        def handler(factory1: MyFactory, factory2: MyFactory):
            return factory1, factory2
        
        instance1, instance2 = handler() # type: ignore
        assert instance1 is not instance2


class TestNamespaceResolution:
    def test_different_classes_same_name(self):
        @singleton
        class Service:
            def __init__(self):
                self.location = "main"
        
        class NamespaceA:
            @singleton
            class Service:
                def __init__(self):
                    self.location = "namespace_a"
        
        @inject
        def handler_main(service: Service):
            return service
        
        @inject
        def handler_ns(service: NamespaceA.Service):
            return service
        
        main_service = handler_main() # type: ignore
        ns_service = handler_ns() # type: ignore
        
        assert main_service.location == "main"
        assert ns_service.location == "namespace_a"
        assert main_service is not ns_service


class TestMixedScopes:
    def test_singleton_and_factory_together(self):
        @singleton
        class SingletonService:
            def __init__(self):
                self.type = "singleton"
        
        @factory
        class FactoryService:
            def __init__(self):
                self.type = "factory"
        
        @inject
        def handler(s: SingletonService, f: FactoryService):
            return s, f
        
        s1, f1 = handler() # type: ignore
        s2, f2 = handler() # type: ignore
        
        assert s1 is s2
        assert f1 is not f2


class TestKeywordOnlyEnforcement:
    """Tests que validan que parámetros no-inyectables son keyword-only."""
    
    def test_non_injectable_param_becomes_keyword_only(self):
        """Parámetro no-inyectable después de inyectable debe ser keyword-only."""
        @singleton
        class MyService:
            def __init__(self):
                self.value = "service"
        
        @inject
        def handler(service: MyService, user_id: str):
            return f"{service.value}:{user_id}"
        
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())
        
        assert params[0].name == "service"
        assert params[0].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        
        assert params[1].name == "user_id"
        assert params[1].kind == inspect.Parameter.KEYWORD_ONLY
    
    def test_multiple_non_injectable_params_all_keyword_only(self):
        """Múltiples parámetros no-inyectables deben ser keyword-only."""
        @singleton
        class ServiceA:
            pass
        
        @inject
        def handler(service: ServiceA, param1: str, param2: int, param3: bool):
            return (param1, param2, param3)
        
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())
        
        assert params[0].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        
        assert params[1].kind == inspect.Parameter.KEYWORD_ONLY
        assert params[2].kind == inspect.Parameter.KEYWORD_ONLY
        assert params[3].kind == inspect.Parameter.KEYWORD_ONLY
    
    def test_only_injectable_params_not_affected(self):
        """Si solo hay parámetros inyectables, no se modifica nada."""
        @singleton
        class ServiceA:
            pass
        
        @singleton
        class ServiceB:
            pass
        
        @inject
        def handler(service_a: ServiceA, service_b: ServiceB):
            return (service_a, service_b)
        
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())
        
        for param in params:
            assert param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    
    def test_only_non_injectable_params_not_affected(self):
        """Si no hay inyectables, la signature no cambia."""
        @inject
        def handler(param1: str, param2: int):
            return (param1, param2)
        
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())
        
        for param in params:
            assert param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD


class TestKeywordOnlyBehavior:
    """Tests que validan el comportamiento en runtime."""
    
    def test_keyword_call_works_correctly(self):
        """Llamadas con keyword arguments funcionan correctamente."""
        @singleton
        class MyService:
            def __init__(self):
                self.value = "injected"
        
        @inject
        def handler(service: MyService, user_id: str):
            return f"{service.value}:{user_id}"
        
        result = handler(user_id="123")  # type: ignore
        assert result == "injected:123"
    
    def test_multiple_keywords_work(self):
        """Múltiples keyword arguments funcionan correctamente."""
        @singleton
        class ServiceA:
            def __init__(self):
                self.name = "ServiceA"
        
        @inject
        def handler(service: ServiceA, x: int, y: str, z: bool):
            return (service.name, x, y, z)
        
        result = handler(x=10, y="test", z=True)  # type: ignore
        assert result == ("ServiceA", 10, "test", True)
    
    def test_positional_call_raises_typeerror(self):
        """Intentar pasar parámetro no-inyectable como posicional debe fallar."""
        @singleton
        class MyService:
            def __init__(self):
                self.value = "service"
        
        @inject
        def handler(service: MyService, user_id: str):
            return f"{service.value}:{user_id}"
        
        with pytest.raises(TypeError) as exc_info:
            handler("123")  # type: ignore
        
        assert "user_id" in str(exc_info.value) or "keyword" in str(exc_info.value).lower()
    
    def test_mixed_injectable_and_non_injectable(self):
        """Mezclar inyectables con no-inyectables funciona con keywords."""
        @singleton
        class ServiceA:
            def __init__(self):
                self.a = "A"
        
        @singleton
        class ServiceB:
            def __init__(self):
                self.b = "B"
        
        @inject
        def handler(s1: ServiceA, param1: str, param2: int):
            return f"{s1.a}:{param1}:{param2}"
        
        result = handler(param1="X", param2=99)  # type: ignore
        assert result == "A:X:99"


class TestKeywordOnlyWithAsync:
    """Tests de keyword-only con funciones async."""
    
    @pytest.mark.asyncio
    async def test_async_function_keyword_only(self):
        """Funciones async también deben tener keyword-only."""
        @singleton
        class AsyncService:
            def __init__(self):
                self.value = "async_service"
        
        @inject
        async def async_handler(service: AsyncService, user_id: str):
            return f"{service.value}:{user_id}"
        
        sig = inspect.signature(async_handler)
        params = list(sig.parameters.values())
        
        assert params[0].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        assert params[1].kind == inspect.Parameter.KEYWORD_ONLY
        
        result = await async_handler(user_id="async123")  # type: ignore
        assert result == "async_service:async123"
    
    @pytest.mark.asyncio
    async def test_async_positional_fails(self):
        """Async con posicional debe fallar."""
        @singleton
        class AsyncService:
            pass
        
        @inject
        async def async_handler(service: AsyncService, param: str):
            return param
        
        with pytest.raises(TypeError):
            await async_handler("value")  # type: ignore


class TestKeywordOnlyEdgeCases:
    """Tests de casos especiales."""
    
    def test_default_values_preserved(self):
        """Valores por defecto se preservan correctamente."""
        @singleton
        class MyService:
            def __init__(self):
                self.value = "service"
        
        @inject
        def handler(service: MyService, optional_param: str = "default"):
            return f"{service.value}:{optional_param}"
        
        result1 = handler()  # type: ignore
        assert result1 == "service:default"
        
        result2 = handler(optional_param="custom")  # type: ignore
        assert result2 == "service:custom"
    
    def test_first_param_non_injectable_then_injectable(self):
        """Test donde el primer parámetro no es inyectable."""
        @singleton
        class S1:
            def __init__(self):
                self.name = "S1"
        
        @inject
        def handler(p1: str, s1: S1, p2: int):
            return (p1, s1.name, p2)
        
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())
        
        assert params[0].name == "p1"
        assert params[0].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        
        assert params[1].name == "s1"
        assert params[1].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        
        assert params[2].name == "p2"
        assert params[2].kind == inspect.Parameter.KEYWORD_ONLY
        
        result = handler("X", p2=10)  # type: ignore
        assert result == ("X", "S1", 10)
    
    def test_no_params_at_all(self):
        """Función sin parámetros no se modifica."""
        @inject
        def no_params():
            return "no_params"
        
        sig = inspect.signature(no_params)
        assert len(sig.parameters) == 0
        
        result = no_params()  # type: ignore
        assert result == "no_params"
    
    def test_self_parameter_ignored(self):
        """El parámetro 'self' debe ser ignorado."""
        @singleton
        class MyService:
            pass
        
        class MyClass:
            @inject
            def method(self, service: MyService, param: str):
                return f"{type(service).__name__}:{param}"
        
        obj = MyClass()
        sig = inspect.signature(obj.method)
        params = list(sig.parameters.values())
        
        assert params[0].name == "service"
        assert params[1].name == "param"
        assert params[1].kind == inspect.Parameter.KEYWORD_ONLY
        
        result = obj.method(param="test")  # type: ignore
        assert "MyService:test" in result


class TestKeywordOnlyDocumentation:
    """Tests que verifican que la signature modificada es visible."""
    
    def test_signature_visible_in_inspect(self):
        """La signature modificada debe ser visible vía inspect."""
        @singleton
        class Service:
            pass
        
        @inject
        def handler(service: Service, x: int, y: str):
            return (x, y)
        
        sig = inspect.signature(handler)
        sig_str = str(sig)
        params = list(sig.parameters.values())
        
        assert "service" in sig_str
        assert "x: int" in sig_str
        assert "y: str" in sig_str
        assert params[1].kind == inspect.Parameter.KEYWORD_ONLY
        assert params[2].kind == inspect.Parameter.KEYWORD_ONLY
    
    def test_help_shows_modified_signature(self):
        """help() debería mostrar la signature modificada."""
        @singleton
        class Service:
            pass
        
        @inject
        def handler(service: Service, param: str):
            """Handler function with injection."""
            return param
        
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            help(handler)
        
        help_text = f.getvalue()
        
        assert "handler" in help_text
        assert "param" in help_text
