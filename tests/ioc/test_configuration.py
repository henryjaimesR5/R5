import pytest
import warnings
from pathlib import Path

from R5.ioc import Container, config


class TestConfigRegistration:
    """Tests para registro y uso básico de @config."""
    
    def test_config_registration(self, test_env_file):
        @config(file=test_env_file)
        class AppConfig:
            app_name: str = "DefaultApp"
            debug: bool = False
        
        assert Container.in_provider(AppConfig)
    
    def test_config_loads_from_env(self, test_env_file):
        @config(file=test_env_file)
        class AppConfig:
            app_name: str = "DefaultApp"
            debug: bool = False
        
        provider = Container.get_provider(AppConfig)
        config_instance = provider()
        
        assert hasattr(config_instance, 'app_name')
        assert isinstance(config_instance.app_name, str)
    
    def test_config_missing_file_raises_error(self):
        with pytest.raises(FileNotFoundError):
            @config(file="/non/existent/file.env")
            class AppConfig:
                app_name: str = "DefaultApp"
            
            provider = Container.get_provider(AppConfig)
            provider()
    
    def test_config_without_file_uses_defaults(self):
        """Test que @config sin file usa solo valores por defecto."""
        @config
        class SimpleConfig:
            app_name: str = "DefaultApp"
            debug: bool = False
        
        assert Container.in_provider(SimpleConfig)
        provider = Container.get_provider(SimpleConfig)
        config_instance = provider()
        assert hasattr(config_instance, 'app_name')
        assert config_instance.app_name == "DefaultApp"
        assert config_instance.debug is False
    
    def test_config_with_empty_parentheses_uses_defaults(self):
        """Test que @config() sin file usa solo valores por defecto."""
        @config()
        class EmptyParensConfig:
            app_name: str = "DefaultApp"
            debug: bool = False
        
        assert Container.in_provider(EmptyParensConfig)
        provider = Container.get_provider(EmptyParensConfig)
        config_instance = provider()
        assert hasattr(config_instance, 'app_name')
        assert config_instance.app_name == "DefaultApp"
        assert config_instance.debug is False
    
    def test_config_with_custom_env_file(self, test_env_file):
        @config(file=test_env_file)
        class CustomEnvConfig:
            app_name: str = "DefaultApp"
            debug: bool = False
        
        assert Container.in_provider(CustomEnvConfig)
        provider = Container.get_provider(CustomEnvConfig)
        config_instance = provider()
        assert hasattr(config_instance, 'app_name')


class TestConfigFormats:
    """Tests para diferentes formatos de configuración."""
    
    def test_load_from_json(self):
        """Test cargar configuración desde JSON."""
        json_file = str(Path(__file__).parent / "fixtures" / "test_config.json")
        
        @config(file=json_file)
        class JsonConfig:
            app_name: str = "DefaultApp"
            debug: bool = False
            port: int = 3000
            host: str = "localhost"
            workers: int = 1
        
        provider = Container.get_provider(JsonConfig)
        config_instance = provider()
        
        assert config_instance.app_name == "TestAppFromJSON"
        assert config_instance.debug is True
        assert config_instance.port == 8080
        assert config_instance.host == "0.0.0.0"
        assert config_instance.workers == 4
    
    def test_load_from_yaml(self):
        """Test cargar configuración desde YAML."""
        yaml_file = str(Path(__file__).parent / "fixtures" / "test_config.yml")
        
        @config(file=yaml_file)
        class YamlConfig:
            app_name: str = "DefaultApp"
            debug: bool = True
            port: int = 3000
            host: str = "localhost"
            workers: int = 1
            features: list[str] = []
        
        provider = Container.get_provider(YamlConfig)
        config_instance = provider()
        
        assert config_instance.app_name == "TestAppFromYAML"
        assert config_instance.debug is False
        assert config_instance.port == 9000
        assert config_instance.host == "localhost"
        assert config_instance.workers == 2
        assert config_instance.features == ["feature1", "feature2", "feature3"]
    
    def test_load_from_properties(self):
        """Test cargar configuración desde Properties."""
        props_file = str(Path(__file__).parent / "fixtures" / "test_config.properties")
        
        @config(file=props_file)
        class PropertiesConfig:
            app_name: str = "DefaultApp"
            debug: bool = False
            port: int = 3000
            host: str = "localhost"
            workers: int = 1
        
        provider = Container.get_provider(PropertiesConfig)
        config_instance = provider()
        
        assert config_instance.app_name == "TestAppFromProperties"
        assert config_instance.debug is True
        assert config_instance.port == 7000
        assert config_instance.host == "127.0.0.1"
        assert config_instance.workers == 8


class TestConfigFallback:
    """Tests para estrategia de fallback a valores por defecto."""
    
    def test_fallback_to_defaults_when_file_not_exists(self):
        """Test usa valores por defecto cuando el archivo no existe."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            @config(file="/non/existent/config.json", required=False)
            class FallbackConfig:
                app_name: str = "DefaultApp"
                debug: bool = False
                port: int = 8080
            
            provider = Container.get_provider(FallbackConfig)
            config_instance = provider()
            
            assert config_instance.app_name == "DefaultApp"
            assert config_instance.debug is False
            assert config_instance.port == 8080
            
            assert len(w) == 1
            assert "not found" in str(w[0].message)
            assert "Using default values" in str(w[0].message)
    
    def test_required_file_raises_error_when_not_exists(self):
        """Test levanta error cuando archivo requerido no existe."""
        with pytest.raises(FileNotFoundError):
            @config(file="/non/existent/config.json", required=True)
            class RequiredConfig:
                app_name: str = "DefaultApp"
            
            provider = Container.get_provider(RequiredConfig)
            provider()
    
    def test_fallback_to_defaults_when_file_corrupt(self):
        """Test usa defaults cuando el archivo está corrupto."""
        corrupt_file = str(Path(__file__).parent / "fixtures" / "corrupt.json")
        
        Path(corrupt_file).parent.mkdir(parents=True, exist_ok=True)
        Path(corrupt_file).write_text("{invalid json content}")
        
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                
                @config(file=corrupt_file, required=False)
                class CorruptFallbackConfig:
                    app_name: str = "DefaultApp"
                    port: int = 3000
                
                provider = Container.get_provider(CorruptFallbackConfig)
                config_instance = provider()
                
                assert config_instance.app_name == "DefaultApp"
                assert config_instance.port == 3000
                
                assert len(w) == 1
                assert "Failed to load config" in str(w[0].message)
        finally:
            Path(corrupt_file).unlink(missing_ok=True)
    
    def test_warning_for_required_field_without_value(self):
        """Test warning para campo requerido sin valor."""
        json_file = str(Path(__file__).parent / "fixtures" / "partial_config.json")
        
        Path(json_file).parent.mkdir(parents=True, exist_ok=True)
        Path(json_file).write_text('{"app_name": "TestApp"}')
        
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                
                @config(file=json_file)
                class PartialConfig:
                    app_name: str = "DefaultApp"
                    port: int
                    host: str
                
                provider = Container.get_provider(PartialConfig)
                config_instance = provider()
                
                assert config_instance.app_name == "TestApp"
                assert config_instance.port is None
                assert config_instance.host is None
                
                warning_messages = [str(warning.message) for warning in w]
                assert any("port" in msg and "no value" in msg for msg in warning_messages)
                assert any("host" in msg and "no value" in msg for msg in warning_messages)
        finally:
            Path(json_file).unlink(missing_ok=True)


class TestConfigTypeConversion:
    """Tests para conversión de tipos desde strings."""
    
    def test_convert_string_to_int(self):
        """Test conversión de string a int."""
        env_file = str(Path(__file__).parent / "fixtures" / "types.env")
        
        Path(env_file).parent.mkdir(parents=True, exist_ok=True)
        Path(env_file).write_text("PORT=8080\n")
        
        try:
            @config(file=env_file)
            class TypeConfig:
                port: int = 3000
            
            provider = Container.get_provider(TypeConfig)
            config_instance = provider()
            
            assert config_instance.port == 8080
            assert isinstance(config_instance.port, int)
        finally:
            Path(env_file).unlink(missing_ok=True)
    
    def test_convert_string_to_bool(self):
        """Test conversión de string a bool."""
        env_file = str(Path(__file__).parent / "fixtures" / "bool_types.env")
        
        Path(env_file).parent.mkdir(parents=True, exist_ok=True)
        Path(env_file).write_text("DEBUG=true\nENABLED=1\nDISABLED=false\n")
        
        try:
            @config(file=env_file)
            class BoolConfig:
                debug: bool = False
                enabled: bool = False
                disabled: bool = True
            
            provider = Container.get_provider(BoolConfig)
            config_instance = provider()
            
            assert config_instance.debug is True
            assert config_instance.enabled is True
            assert config_instance.disabled is False
        finally:
            Path(env_file).unlink(missing_ok=True)
    
    def test_convert_string_to_list(self):
        """Test conversión de string CSV a list."""
        env_file = str(Path(__file__).parent / "fixtures" / "list_types.env")
        
        Path(env_file).parent.mkdir(parents=True, exist_ok=True)
        Path(env_file).write_text("FEATURES=feature1,feature2,feature3\n")
        
        try:
            @config(file=env_file)
            class ListConfig:
                features: list[str] = []
            
            provider = Container.get_provider(ListConfig)
            config_instance = provider()
            
            assert config_instance.features == ["feature1", "feature2", "feature3"]
            assert isinstance(config_instance.features, list)
        finally:
            Path(env_file).unlink(missing_ok=True)
    
    def test_convert_string_to_float(self):
        """Test conversión de string a float."""
        env_file = str(Path(__file__).parent / "fixtures" / "float_types.env")
        
        Path(env_file).parent.mkdir(parents=True, exist_ok=True)
        Path(env_file).write_text("RATIO=3.14\nPERCENT=0.85\n")
        
        try:
            @config(file=env_file)
            class FloatConfig:
                ratio: float = 1.0
                percent: float = 0.0
            
            provider = Container.get_provider(FloatConfig)
            config_instance = provider()
            
            assert config_instance.ratio == 3.14
            assert config_instance.percent == 0.85
            assert isinstance(config_instance.ratio, float)
        finally:
            Path(env_file).unlink(missing_ok=True)
    
    def test_convert_string_to_set(self):
        """Test conversión de string CSV a set."""
        env_file = str(Path(__file__).parent / "fixtures" / "set_types.env")
        
        Path(env_file).parent.mkdir(parents=True, exist_ok=True)
        Path(env_file).write_text("TAGS=python,fastapi,async\n")
        
        try:
            @config(file=env_file)
            class SetConfig:
                tags: set[str] = set()
            
            provider = Container.get_provider(SetConfig)
            config_instance = provider()
            
            assert config_instance.tags == {"python", "fastapi", "async"}
            assert isinstance(config_instance.tags, set)
        finally:
            Path(env_file).unlink(missing_ok=True)
    
    def test_convert_string_to_tuple(self):
        """Test conversión de string CSV a tuple."""
        env_file = str(Path(__file__).parent / "fixtures" / "tuple_types.env")
        
        Path(env_file).parent.mkdir(parents=True, exist_ok=True)
        Path(env_file).write_text("COORDS=10,20\n")
        
        try:
            @config(file=env_file)
            class TupleConfig:
                coords: tuple[str, str] = ("0", "0")
            
            provider = Container.get_provider(TupleConfig)
            config_instance = provider()
            
            assert config_instance.coords == ("10", "20")
            assert isinstance(config_instance.coords, tuple)
        finally:
            Path(env_file).unlink(missing_ok=True)


class TestConfigEnvOverride:
    """Tests para override con variables de entorno."""
    
    def test_env_override_enabled(self):
        """Test que variables de entorno sobrescriben valores del archivo."""
        import os
        
        env_file = str(Path(__file__).parent / "fixtures" / "env_override.env")
        Path(env_file).parent.mkdir(parents=True, exist_ok=True)
        Path(env_file).write_text("PORT=8080\nHOST=localhost\n")
        
        os.environ["PORT"] = "9000"
        os.environ["HOST"] = "0.0.0.0"
        
        try:
            @config(file=env_file, env_override=True)
            class EnvConfig:
                port: int = 3000
                host: str = "127.0.0.1"
            
            provider = Container.get_provider(EnvConfig)
            config_instance = provider()
            
            assert config_instance.port == 9000
            assert config_instance.host == "0.0.0.0"
        finally:
            Path(env_file).unlink(missing_ok=True)
            os.environ.pop("PORT", None)
            os.environ.pop("HOST", None)
    
    def test_env_override_disabled(self):
        """Test que con env_override=False no se usan variables de entorno."""
        import os
        
        env_file = str(Path(__file__).parent / "fixtures" / "no_env_override.env")
        Path(env_file).parent.mkdir(parents=True, exist_ok=True)
        Path(env_file).write_text("PORT=8080\n")
        
        os.environ["PORT"] = "9000"
        
        try:
            @config(file=env_file, env_override=False)
            class NoEnvConfig:
                port: int = 3000
            
            provider = Container.get_provider(NoEnvConfig)
            config_instance = provider()
            
            assert config_instance.port == 8080
        finally:
            Path(env_file).unlink(missing_ok=True)
            os.environ.pop("PORT", None)
    
    def test_env_override_with_no_file(self):
        """Test que env_override funciona sin archivo de configuración."""
        import os
        
        os.environ["APP_NAME"] = "EnvApp"
        os.environ["DEBUG"] = "true"
        
        try:
            @config(env_override=True)
            class EnvOnlyConfig:
                app_name: str = "DefaultApp"
                debug: bool = False
            
            provider = Container.get_provider(EnvOnlyConfig)
            config_instance = provider()
            
            assert config_instance.app_name == "EnvApp"
            assert config_instance.debug is True
        finally:
            os.environ.pop("APP_NAME", None)
            os.environ.pop("DEBUG", None)


class TestConfigCaseSensitivity:
    """Tests para case sensitivity en matching de claves."""
    
    def test_case_insensitive_default(self):
        """Test que por defecto el matching es case-insensitive."""
        json_file = str(Path(__file__).parent / "fixtures" / "case_test.json")
        Path(json_file).parent.mkdir(parents=True, exist_ok=True)
        Path(json_file).write_text('{"DATABASE_URL": "postgres://db", "Api_Key": "secret123"}')
        
        try:
            @config(file=json_file)
            class CaseInsensitiveConfig:
                database_url: str = "default"
                api_key: str = "default"
            
            provider = Container.get_provider(CaseInsensitiveConfig)
            config_instance = provider()
            
            assert config_instance.database_url == "postgres://db"
            assert config_instance.api_key == "secret123"
        finally:
            Path(json_file).unlink(missing_ok=True)
    
    def test_case_sensitive_enabled(self):
        """Test que con case_sensitive=True solo matchea exacto."""
        json_file = str(Path(__file__).parent / "fixtures" / "case_sensitive_test.json")
        Path(json_file).parent.mkdir(parents=True, exist_ok=True)
        Path(json_file).write_text('{"database_url": "postgres://db", "API_KEY": "wrong"}')
        
        try:
            @config(file=json_file, case_sensitive=True)
            class CaseSensitiveConfig:
                database_url: str = "default_db"
                api_key: str = "default_key"
            
            provider = Container.get_provider(CaseSensitiveConfig)
            config_instance = provider()
            
            assert config_instance.database_url == "postgres://db"
            assert config_instance.api_key == "default_key"
        finally:
            Path(json_file).unlink(missing_ok=True)
