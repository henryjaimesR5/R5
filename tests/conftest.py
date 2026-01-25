import pytest


@pytest.fixture(autouse=True)
def clear_container():
    """
    Fixture global que limpia el Container de IoC entre tests.
    
    Esto asegura que cada test comience con un Container limpio,
    evitando que los registros de un test afecten a otros.
    """
    from R5.ioc.container import Container
    
    snapshot = Container.snapshot()
    
    yield
    
    Container.restore(snapshot)


