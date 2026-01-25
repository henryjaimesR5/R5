import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def test_env_file():
    """Fixture específico para tests de IoC que necesitan archivos de configuración."""
    return str(Path(__file__).parent / "fixtures" / ".env")
