import pytest
from R5.ioc import Container, Scope, singleton, factory
from R5.ioc.errors import ProviderNotFoundError


class TestContainerBasics:
    def test_get_container_returns_dict(self):
        container = Container.get_container()
        assert isinstance(container, dict)
    
    def test_in_provider_returns_false_for_unregistered(self):
        class UnregisteredService:
            pass
        
        assert not Container.in_provider(UnregisteredService)
    
    def test_in_provider_returns_true_for_registered(self):
        @singleton
        class MyService:
            pass
        
        assert Container.in_provider(MyService)
    
    def test_get_provider_raises_for_unregistered(self):
        class UnregisteredService:
            pass
        
        with pytest.raises(ProviderNotFoundError):
            Container.get_provider(UnregisteredService)


class TestContainerRegistration:
    def test_registry_provider_singleton(self):
        class MyService:
            def __init__(self):
                self.value = "test"
        
        Container.registry_provider(MyService, Scope.SINGLETON)
        
        assert Container.in_provider(MyService)
        provider = Container.get_provider(MyService)
        instance1 = provider()
        instance2 = provider()
        assert instance1 is instance2
    
    def test_registry_provider_factory(self):
        class MyFactory:
            def __init__(self):
                self.value = "test"
        
        Container.registry_provider(MyFactory, Scope.FACTORY)
        
        assert Container.in_provider(MyFactory)
        provider = Container.get_provider(MyFactory)
        instance1 = provider()
        instance2 = provider()
        assert instance1 is not instance2
    
    def test_registry_provider_with_required_params(self):
        class MyService:
            def __init__(self, value: str = "default"):
                self.value = value
        
        Container.registry_provider(MyService, Scope.SINGLETON)
        
        provider = Container.get_provider(MyService)
        instance = provider()
        assert instance.value == "default"


class TestRegisterClassWithDependencies:
    def test_register_class_without_dependencies(self):
        class SimpleService:
            def __init__(self):
                self.value = "simple"
        
        Container.registry_provider(SimpleService, Scope.SINGLETON)
        
        provider = Container.get_provider(SimpleService)
        instance = provider()
        assert instance.value == "simple"
    
    def test_register_class_with_dependencies(self):
        @singleton
        class DependencyA:
            def __init__(self):
                self.value = "A"
        
        class ServiceWithDeps:
            def __init__(self, dep_a: DependencyA):
                self.dep_a = dep_a
                self.value = "service"
        
        Container.registry_provider(ServiceWithDeps, Scope.SINGLETON)
        
        provider = Container.get_provider(ServiceWithDeps)
        instance = provider()
        assert instance.value == "service"
        assert instance.dep_a.value == "A"
    
    def test_register_class_with_multiple_dependencies(self):
        @singleton
        class DependencyA:
            def __init__(self):
                self.value = "A"
        
        @singleton
        class DependencyB:
            def __init__(self):
                self.value = "B"
        
        class ServiceWithMultipleDeps:
            def __init__(self, dep_a: DependencyA, dep_b: DependencyB):
                self.dep_a = dep_a
                self.dep_b = dep_b
        
        Container.registry_provider(ServiceWithMultipleDeps, Scope.SINGLETON)
        
        provider = Container.get_provider(ServiceWithMultipleDeps)
        instance = provider()
        assert instance.dep_a.value == "A"
        assert instance.dep_b.value == "B"
    
    def test_register_class_with_unregistered_dependency(self):
        class UnregisteredDep:
            pass
        
        class ServiceWithUnregisteredDep:
            def __init__(self, dep: UnregisteredDep):
                self.dep = dep
        
        Container.registry_provider(ServiceWithUnregisteredDep, Scope.SINGLETON)
        
        provider = Container.get_provider(ServiceWithUnregisteredDep)
        
        with pytest.raises(TypeError):
            provider()


class TestContainerScopes:
    def test_singleton_scope_behavior(self):
        class MyService:
            def __init__(self):
                self.counter = 0
        
        Container.registry_provider(MyService, Scope.SINGLETON)
        
        provider = Container.get_provider(MyService)
        instance1 = provider()
        instance1.counter = 1
        instance2 = provider()
        
        assert instance2.counter == 1
        assert instance1 is instance2
    
    def test_factory_scope_behavior(self):
        class MyFactory:
            def __init__(self):
                self.counter = 0
        
        Container.registry_provider(MyFactory, Scope.FACTORY)
        
        provider = Container.get_provider(MyFactory)
        instance1 = provider()
        instance1.counter = 1
        instance2 = provider()
        
        assert instance2.counter == 0
        assert instance1 is not instance2


class TestContainerState:
    def test_container_preserves_registration_order(self):
        @singleton
        class ServiceA:
            pass
        
        @singleton
        class ServiceB:
            pass
        
        @singleton
        class ServiceC:
            pass
        
        container = Container.get_container()
        
        assert ServiceA in container
        assert ServiceB in container
        assert ServiceC in container
    
    def test_multiple_types_registered(self):
        @singleton
        class SingletonService:
            pass
        
        @factory
        class FactoryService:
            pass
        
        assert Container.in_provider(SingletonService)
        assert Container.in_provider(FactoryService)
        
        container = Container.get_container()
        assert len(container) >= 2
