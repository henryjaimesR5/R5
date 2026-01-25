"""
Módulo de configuración para el framework R5.

Proporciona el decorador @config y los loaders para múltiples formatos de configuración.

Mejoras:
- Carga única del archivo (no repetida en cada instancia)
- Cache de configuración con @lru_cache
- Mejor conversión de tipos (int, float, bool, list, dict, set, tuple)
- Soporte para variables de entorno como override
- Matching flexible de claves (case-insensitive por defecto)
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar, overload, get_type_hints, get_origin, get_args
import warnings
import json
import os
from functools import lru_cache

from R5.ioc.container import Container, Scope


T = TypeVar("T")


# ============================================================================
# Configuration Loaders (Private)
# ============================================================================

class _ConfigLoader(ABC):
    @abstractmethod
    def can_load(self, file_path: Path) -> bool:
        pass
    
    @abstractmethod
    def load(self, file_path: Path) -> dict[str, Any]:
        pass


class _EnvLoader(_ConfigLoader):
    def can_load(self, file_path: Path) -> bool:
        name = file_path.name
        return (
            file_path.suffix == '.env' or 
            name == '.env' or 
            name.startswith('.env.') or
            name.startswith('.env')
        )
    
    def load(self, file_path: Path) -> dict[str, Any]:
        config = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    config[key] = value
        return config


class _JsonLoader(_ConfigLoader):
    def can_load(self, file_path: Path) -> bool:
        return file_path.suffix == '.json'
    
    def load(self, file_path: Path) -> dict[str, Any]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)


class _YamlLoader(_ConfigLoader):
    _yaml_module = None
    
    @classmethod
    def _get_yaml(cls):
        if cls._yaml_module is None:
            try:
                import yaml
                cls._yaml_module = yaml
            except ImportError as e:
                raise ImportError(
                    "YAML support requires PyYAML. Install it with: pip install pyyaml"
                ) from e
        return cls._yaml_module
    
    def can_load(self, file_path: Path) -> bool:
        return file_path.suffix in {'.yml', '.yaml'}
    
    def load(self, file_path: Path) -> dict[str, Any]:
        yaml = self._get_yaml()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict):
            return {}
        
        return data


class _PropertiesLoader(_ConfigLoader):
    def can_load(self, file_path: Path) -> bool:
        return file_path.suffix == '.properties'
    
    def load(self, file_path: Path) -> dict[str, Any]:
        config = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('!'):
                    continue
                if '=' in line or ':' in line:
                    separator = '=' if '=' in line else ':'
                    key, value = line.split(separator, 1)
                    config[key.strip()] = value.strip()
        return config


class _ConfigLoaderFactory:
    _loaders: list[_ConfigLoader] = [
        _EnvLoader(),
        _JsonLoader(),
        _YamlLoader(),
        _PropertiesLoader(),
    ]
    
    @classmethod
    def get_loader(cls, file_path: Path) -> _ConfigLoader:
        for loader in cls._loaders:
            if loader.can_load(file_path):
                return loader
        
        raise ValueError(
            f"No loader found for file: {file_path}. "
            f"Supported formats: .env, .json, .yml, .yaml, .properties"
        )
    
    @classmethod
    @lru_cache(maxsize=32)
    def load_config(cls, file_path: str) -> dict[str, Any]:
        """Carga y cachea la configuración del archivo."""
        loader = cls.get_loader(Path(file_path))
        return loader.load(Path(file_path))


class _TypeConverter:
    """Convierte valores de string a tipos específicos."""
    
    @staticmethod
    def convert(value: Any, target_type: Any) -> Any:
        if value is None:
            return None
        
        origin = get_origin(target_type)
        
        if origin is list:
            return _TypeConverter._convert_to_list(value, target_type)
        elif origin is dict:
            return _TypeConverter._convert_to_dict(value)
        elif origin is set:
            return _TypeConverter._convert_to_set(value, target_type)
        elif origin is tuple:
            return _TypeConverter._convert_to_tuple(value, target_type)
        elif target_type == bool:
            return _TypeConverter._convert_to_bool(value)
        elif target_type in {int, float, str}:
            return _TypeConverter._convert_primitive(value, target_type)
        
        return value
    
    @staticmethod
    def _convert_to_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    @staticmethod
    def _convert_primitive(value: Any, target_type: type) -> Any:
        if isinstance(value, target_type):
            return value
        if isinstance(value, str):
            try:
                return target_type(value)
            except (ValueError, TypeError):
                return value
        return value
    
    @staticmethod
    def _convert_to_list(value: Any, target_type: Any) -> list:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [v.strip() for v in value.split(',') if v.strip()]
        return list(value) if hasattr(value, '__iter__') else [value]
    
    @staticmethod
    def _convert_to_set(value: Any, target_type: Any) -> set:
        if isinstance(value, set):
            return value
        if isinstance(value, str):
            return {v.strip() for v in value.split(',') if v.strip()}
        return set(value) if hasattr(value, '__iter__') else {value}
    
    @staticmethod
    def _convert_to_tuple(value: Any, target_type: Any) -> tuple:
        if isinstance(value, tuple):
            return value
        if isinstance(value, str):
            return tuple(v.strip() for v in value.split(',') if v.strip())
        return tuple(value) if hasattr(value, '__iter__') else (value,)
    
    @staticmethod
    def _convert_to_dict(value: Any) -> dict:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        return {}


def _normalize_key(key: str, case_sensitive: bool = False) -> str:
    """Normaliza claves para matching."""
    return key if case_sensitive else key.lower()


def _match_config_key(attr_name: str, config_data: dict[str, Any], case_sensitive: bool = False) -> Any | None:
    """Busca una clave en el config con soporte para múltiples formatos."""
    if case_sensitive:
        return config_data.get(attr_name)
    
    normalized_attr = _normalize_key(attr_name, case_sensitive)
    for key, value in config_data.items():
        if _normalize_key(key, case_sensitive) == normalized_attr:
            return value
    
    return None


# ============================================================================
# Configuration Decorator
# ============================================================================

@overload
def config(
    cls: type[T], 
    *, 
    file: str | None = None, 
    required: bool = True,
    env_override: bool = True,
    case_sensitive: bool = False,
) -> type[T]: ...


@overload
def config(
    cls: None = None, 
    *, 
    file: str | None = None, 
    required: bool = True,
    env_override: bool = True,
    case_sensitive: bool = False,
) -> Callable[[type[T]], type[T]]: ...


def config(
    cls: type[T] | None = None, 
    *, 
    file: str | None = None, 
    required: bool = True,
    env_override: bool = True,
    case_sensitive: bool = False,
) -> type[T] | Callable[[type[T]], type[T]]:
    """Decorador para clases de configuración con carga optimizada.
    
    Soporta múltiples formatos: .env, .json, .yml, .yaml, .properties
    
    Mejoras:
    - Carga única del archivo (no repetida en cada instancia)
    - Cache automático con @lru_cache
    - Soporte para variables de entorno como override
    - Mejor conversión de tipos (int, float, bool, list, dict, set, tuple)
    - Matching flexible de claves
    
    Args:
        file: Ruta al archivo de configuración
        required: Si True, el archivo debe existir
        env_override: Si True, variables de entorno sobreescriben valores del archivo
        case_sensitive: Si True, respeta mayúsculas/minúsculas en nombres de campos
    
    Ejemplo:
        @config(file='config.json', env_override=True)
        class MyConfig:
            host: str = 'localhost'
            port: int = 8080
    """
    def decorator(cls_to_decorate: type[T]) -> type[T]:
        config_data = _load_config_data(file, required)
        type_hints = get_type_hints(cls_to_decorate)
        
        class ConfigClass:
            _config_data = config_data
            _type_hints = type_hints
            _env_override = env_override
            _case_sensitive = case_sensitive
            
            def __init__(self, **kwargs: Any):
                processed_attrs = set()
                
                for attr_name, attr_type in self._type_hints.items():
                    if attr_name.startswith('_'):
                        continue
                    
                    processed_attrs.add(attr_name)
                    value = self._get_config_value(attr_name, attr_type)
                    setattr(self, attr_name, value)
                
                for attr_name in dir(cls_to_decorate):
                    if attr_name.startswith('_') or attr_name in processed_attrs:
                        continue
                    
                    attr_value = getattr(cls_to_decorate, attr_name, None)
                    if callable(attr_value):
                        continue
                    
                    setattr(self, attr_name, attr_value)
                
                for key, value in kwargs.items():
                    setattr(self, key, value)
            
            def _get_config_value(self, attr_name: str, attr_type: Any) -> Any:
                value = None
                source = "default"
                
                if self._env_override:
                    env_key = attr_name.upper()
                    env_value = os.environ.get(env_key)
                    if env_value is not None:
                        value = env_value
                        source = "env"
                
                if value is None and self._config_data:
                    file_value = _match_config_key(attr_name, self._config_data, self._case_sensitive)
                    if file_value is not None:
                        value = file_value
                        source = "file"
                
                if value is None and hasattr(cls_to_decorate, attr_name):
                    value = getattr(cls_to_decorate, attr_name)
                    source = "default"
                
                if value is None and not _is_optional(attr_type):
                    warnings.warn(
                        f"Required field '{attr_name}' in {cls_to_decorate.__name__} "
                        f"has no value in config file, environment, or default.",
                        UserWarning,
                    )
                    return None
                
                if value is not None and source in ("env", "file"):
                    value = _TypeConverter.convert(value, attr_type)
                
                return value
        
        ConfigClass.__name__ = cls_to_decorate.__name__
        ConfigClass.__qualname__ = cls_to_decorate.__qualname__
        ConfigClass.__module__ = cls_to_decorate.__module__
        ConfigClass.__annotations__ = getattr(cls_to_decorate, '__annotations__', {})
        
        Container.registry_provider(ConfigClass, Scope.SINGLETON)
        Container.alias_provider(cls_to_decorate, ConfigClass)
        
        return cls_to_decorate
    
    if cls is None:
        return decorator
    else:
        return decorator(cls)


def _is_optional(type_hint: Any) -> bool:
    """Verifica si un type hint es Optional (Union con None)."""
    origin = get_origin(type_hint)
    if origin is None:
        return False
    
    import typing
    if hasattr(typing, 'UnionType') and origin is typing.UnionType:
        args = get_args(type_hint)
        return type(None) in args
    
    if origin is typing.Union:
        args = get_args(type_hint)
        return type(None) in args
    
    return False


def _load_config_data(file: str | None, required: bool) -> dict[str, Any]:
    """Carga los datos de configuración del archivo (una sola vez)."""
    if file is None:
        return {}
    
    resolved_file = file
    if not Path(resolved_file).is_absolute():
        resolved_file = str(Path.cwd() / file)
    
    file_path = Path(resolved_file)
    
    if not file_path.exists():
        if required:
            raise FileNotFoundError(
                f"Configuration file {file_path} not found"
            )
        warnings.warn(
            f"Configuration file {file_path} not found. Using default values.",
            UserWarning,
        )
        return {}
    
    try:
        return _ConfigLoaderFactory.load_config(str(file_path))
    except Exception as e:
        if required:
            raise RuntimeError(
                f"Failed to load config from {file_path}: {e}"
            ) from e
        warnings.warn(
            f"Failed to load config from {file_path}: {e}. Using defaults.",
            UserWarning,
        )
        return {}
