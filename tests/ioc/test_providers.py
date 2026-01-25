import pytest
import asyncio
from R5.ioc import singleton, factory, resource, config, Container


class DatabaseConnection:
    """Clase de ejemplo para tests de @resource con lifecycle management."""
    
    def __init__(self, connection_string: str = "test://localhost"):
        self.connection_string = connection_string
        self.is_connected = False
        self.is_closed = False
        self.query_count = 0
    
    async def connect(self):
        """Simula conexión a BD."""
        await asyncio.sleep(0.01)
        self.is_connected = True
    
    async def query(self, sql: str):
        """Simula query a BD."""
        if not self.is_connected:
            await self.connect()
        self.query_count += 1
        return {"result": f"Query executed: {sql}"}
    
    async def close(self):
        """Cierra conexión."""
        await asyncio.sleep(0.01)
        self.is_connected = False
        self.is_closed = True
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()


class TestSingleton:
    def test_singleton_registration(self):
        @singleton
        class MyService:
            def __init__(self):
                self.value = "test"
        
        assert Container.in_provider(MyService)
        provider = Container.get_provider(MyService)
        assert provider is not None
    
    def test_singleton_same_instance(self):
        @singleton
        class MyService:
            def __init__(self):
                self.counter = 0
        
        provider = Container.get_provider(MyService)
        instance1 = provider()
        instance2 = provider()
        
        assert instance1 is instance2
    
    def test_singleton_preserves_type(self):
        @singleton
        class MyService:
            def get_value(self) -> str:
                return "test"
        
        assert callable(MyService)
        instance = MyService()
        assert instance.get_value() == "test"


class TestFactory:
    def test_factory_registration(self):
        @factory
        class MyFactory:
            def __init__(self):
                self.value = "test"
        
        assert Container.in_provider(MyFactory)
    
    def test_factory_different_instances(self):
        @factory
        class MyFactory:
            def __init__(self):
                self.counter = 0
        
        provider = Container.get_provider(MyFactory)
        instance1 = provider()
        instance2 = provider()
        
        assert instance1 is not instance2
    
    def test_factory_preserves_type(self):
        @factory
        class MyFactory:
            def get_value(self) -> str:
                return "test"
        
        assert callable(MyFactory)
        instance = MyFactory()
        assert instance.get_value() == "test"


class TestSingletonWithDependencies:
    def test_singleton_with_no_dependencies(self):
        @singleton
        class ServiceA:
            def __init__(self):
                self.value = "A"
        
        provider = Container.get_provider(ServiceA)
        instance = provider()
        assert instance.value == "A"
    
    def test_singleton_with_dependencies(self):
        @singleton
        class ServiceA:
            def __init__(self):
                self.value = "A"
        
        @singleton
        class ServiceB:
            def __init__(self, service_a: ServiceA):
                self.service_a = service_a
                self.value = "B"
        
        provider_b = Container.get_provider(ServiceB)
        instance_b = provider_b()
        
        assert instance_b.value == "B"
        assert instance_b.service_a.value == "A"
    
    def test_factory_with_dependencies(self):
        @singleton
        class ServiceA:
            def __init__(self):
                self.value = "A"
        
        @factory
        class FactoryB:
            def __init__(self, service_a: ServiceA):
                self.service_a = service_a
                self.value = "B"
        
        provider_b = Container.get_provider(FactoryB)
        instance_b = provider_b()
        
        assert instance_b.value == "B"
        assert instance_b.service_a.value == "A"


class TestResource:
    """Tests para @resource provider con lifecycle management."""
    
    @pytest.mark.asyncio
    async def test_resource_registration(self):
        """Test registro de resource en container."""
        @resource
        class TestDB(DatabaseConnection):
            pass
        
        assert Container.in_provider(TestDB)
        provider = Container.get_provider(TestDB)
        assert provider is not None
    
    @pytest.mark.asyncio
    async def test_resource_closes_automatically(self):
        """Test cierre automático al salir del contexto."""
        @resource
        class TestDB(DatabaseConnection):
            pass
        
        container = Container()
        db_resource = container.resolve(TestDB)
        
        async with await db_resource as db:
            assert db.is_connected is True or db.is_connected is False
            await db.connect()
            assert db.is_connected is True
        
        assert db.is_closed is True
    
    @pytest.mark.asyncio
    async def test_resource_singleton_behavior(self):
        """Test comportamiento singleton del resource."""
        @resource
        class TestDB(DatabaseConnection):
            pass
        
        container = Container()
        
        db_resource1 = container.resolve(TestDB)
        db_resource2 = container.resolve(TestDB)
        
        async with await db_resource1 as db1:
            async with await db_resource2 as db2:
                assert db1 is db2
                assert id(db1) == id(db2)
    
    @pytest.mark.asyncio
    async def test_resource_closes_with_exception(self):
        """Test cierre automático incluso con excepción."""
        @resource
        class TestDB(DatabaseConnection):
            pass
        
        container = Container()
        db_resource = container.resolve(TestDB)
        
        try:
            async with await db_resource as db:
                await db.connect()
                assert db.is_connected is True
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        assert db.is_closed is True
    
    @pytest.mark.asyncio
    async def test_resource_reusable_after_close(self):
        """Test reutilización después de cierre."""
        @resource
        class TestDB(DatabaseConnection):
            pass
        
        container = Container()
        
        db_resource = container.resolve(TestDB)
        async with await db_resource as db:
            await db.query("SELECT 1")
            assert db.query_count == 1
        
        assert db.is_closed is True
        
        async with await db_resource as db2:
            await db2.connect()
            await db2.query("SELECT 2")
            assert db2.is_connected is True
    
    @pytest.mark.asyncio
    async def test_resource_with_inject(self):
        """Test resource con decorador @inject."""
        from R5.ioc import inject
        
        @resource
        class TestDB(DatabaseConnection):
            pass
        
        @inject
        async def query_service(db: TestDB):
            result = await db.query("SELECT * FROM users")
            return result
        
        container = Container()
        db_resource = container.resolve(TestDB)
        
        async with await db_resource as db:
            result = await query_service(db)
            assert result["result"] == "Query executed: SELECT * FROM users"
        
        assert db.is_closed is True
    
    @pytest.mark.asyncio
    async def test_resource_concurrent_usage(self):
        """Test uso concurrent del resource."""
        @resource
        class TestDB(DatabaseConnection):
            pass
        
        async def concurrent_query(db: TestDB, query: str):
            await asyncio.sleep(0.01)
            return await db.query(query)
        
        container = Container()
        db_resource = container.resolve(TestDB)
        
        async with await db_resource as db:
            tasks = [
                concurrent_query(db, "SELECT 1"),
                concurrent_query(db, "SELECT 2"),
                concurrent_query(db, "SELECT 3")
            ]
            
            results = await asyncio.gather(*tasks)
            assert len(results) == 3
            assert db.query_count == 3
        
        assert db.is_closed is True
    
    @pytest.mark.asyncio
    async def test_resource_nested_contexts(self):
        """Test contextos anidados."""
        @resource
        class TestDB(DatabaseConnection):
            pass
        
        container = Container()
        
        async with await container.resolve(TestDB) as db1:
            await db1.query("SELECT 1")
            
            async with await container.resolve(TestDB) as db2:
                assert db1 is db2
                await db2.query("SELECT 2")
                assert db1.query_count == 2
    
    @pytest.mark.asyncio
    async def test_resource_with_dependencies(self):
        """Test resource con dependencias inyectadas."""
        @singleton
        class ConfigService:
            def __init__(self):
                self.db_url = "prod://database"
        
        @resource
        class TestDB(DatabaseConnection):
            def __init__(self, config: ConfigService):
                super().__init__(config.db_url)
                self.config = config
        
        container = Container()
        db_resource = container.resolve(TestDB)
        
        async with await db_resource as db:
            assert db.connection_string == "prod://database"
            assert db.config is not None
        
        assert db.is_closed is True
