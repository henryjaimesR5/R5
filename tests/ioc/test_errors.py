import pytest
from R5.ioc import (
    singleton,
    inject,
    Container,
    Scope,
    CircularDependencyError,
    ProviderNotFoundError,
    DependencyInjectionError,
)


class TestCircularDependencies:
    def test_circular_dependency_detection(self):
        @singleton
        class ServiceA:
            def __init__(self, service_b: "ServiceB"):
                self.service_b = service_b
        
        @singleton
        class ServiceB:
            def __init__(self, service_a: ServiceA):
                self.service_a = service_a
        
        @inject
        def handler(service_a: ServiceA):
            return service_a
        
        with pytest.raises(DependencyInjectionError):
            handler()
    
    def test_self_circular_dependency(self):
        @singleton
        class SelfReferencing:
            def __init__(self, self_ref: "SelfReferencing"):
                self.self_ref = self_ref
        
        @inject
        def handler(service: SelfReferencing):
            return service
        
        with pytest.raises(DependencyInjectionError):
            handler()
    
    def test_three_way_circular_dependency(self):
        @singleton
        class ServiceA:
            def __init__(self, service_c: "ServiceC"):
                self.service_c = service_c
        
        @singleton
        class ServiceB:
            def __init__(self, service_a: ServiceA):
                self.service_a = service_a
        
        @singleton
        class ServiceC:
            def __init__(self, service_b: ServiceB):
                self.service_b = service_b
        
        @inject
        def handler(service_a: ServiceA):
            return service_a
        
        with pytest.raises(DependencyInjectionError):
            handler()


class TestProviderNotFound:
    def test_provider_not_found_error(self):
        class UnregisteredService:
            pass
        
        with pytest.raises(ProviderNotFoundError) as exc_info:
            Container.get_provider(UnregisteredService)
        
        error = exc_info.value
        assert "UnregisteredService" in str(error)
        assert "not found in container" in str(error)
    
    def test_provider_not_found_shows_available(self):
        @singleton
        class RegisteredService:
            pass
        
        class UnregisteredService:
            pass
        
        with pytest.raises(ProviderNotFoundError) as exc_info:
            Container.get_provider(UnregisteredService)
        
        error = exc_info.value
        assert len(error.available_providers) > 0
        assert "Available providers:" in str(error)
    
    def test_injection_provider_not_found(self):
        class UnregisteredService:
            pass
        
        @inject
        def handler(service: UnregisteredService = None, default="default"):
            return default if service is None else service
        
        result = handler()
        assert result == "default"


class TestDependencyInjectionErrors:
    def test_injection_error_contains_context(self):
        @singleton
        class BrokenService:
            def __init__(self, missing_dep: "NonExistentDep"):
                self.missing_dep = missing_dep
        
        @inject
        def my_handler(service: BrokenService):
            return service
        
        with pytest.raises(DependencyInjectionError) as exc_info:
            my_handler()
        
        error = exc_info.value
        assert error.provider_type == BrokenService
        assert error.param_name == "service"
        assert error.func_name == "my_handler"


class TestTypeValidation:
    def test_inject_without_type_annotation(self):
        @singleton
        class MyService:
            def __init__(self):
                self.value = "service"
        
        @inject
        def handler(manual_value="default"):
            return manual_value
        
        result = handler()
        assert result == "default"
    
    def test_inject_with_invalid_type(self):
        @singleton
        class MyService:
            pass
        
        @inject
        def handler(service: str = "default"):
            return service
        
        result = handler()
        assert result == "default"


class TestCircularDependencyError:
    def test_circular_dependency_error_message(self):
        error = CircularDependencyError(['ServiceA', 'ServiceB', 'ServiceA'])
        
        assert hasattr(error, 'dependency_chain')
        assert error.dependency_chain == ['ServiceA', 'ServiceB', 'ServiceA']
        assert "Circular dependency detected:" in str(error)
        assert "ServiceA -> ServiceB -> ServiceA" in str(error)
    
    def test_circular_dependency_chain_formatting(self):
        chain = ['test_module.ServiceA', 'test_module.ServiceB', 'test_module.ServiceC', 'test_module.ServiceA']
        error = CircularDependencyError(chain)
        
        error_str = str(error)
        assert "Circular dependency detected:" in error_str
        assert " -> " in error_str
        
        for service_name in chain:
            assert service_name in error_str
    
    def test_circular_dependency_single_element(self):
        error = CircularDependencyError(['ServiceA'])
        assert len(error.dependency_chain) == 1
        assert "ServiceA" in str(error)


class TestWarnings:
    def test_duplicate_registration_warning(self):
        import warnings
        
        @singleton
        class MyService:
            pass
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            Container.registry_provider(MyService, Scope.SINGLETON)
            
            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "being overwritten" in str(w[0].message)
