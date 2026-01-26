from typing import TypeVar, Optional, Type, Callable, get_origin, get_args, Union
from dataclasses import dataclass, field, is_dataclass, fields
import httpx
import asyncio
import warnings

T = TypeVar('T')

@dataclass
class Result:
    """Wrapper para respuestas HTTP con handlers encadenados.
    
    Atributos:
        response: httpx.Response (puede ser None si hubo excepción)
        request: httpx.Request (puede ser None si hubo excepción)
        status: Código HTTP (0 si hubo excepción antes de respuesta)
        exception: Excepción capturada (None si no hubo error)
    """
    response: Optional[httpx.Response] = None
    request: Optional[httpx.Request] = None
    status: int = 0
    exception: Optional[Exception] = None
    
    @staticmethod
    def from_response(response: httpx.Response) -> 'Result':
        """Crea Result desde httpx.Response exitosa."""
        return Result(
            response=response,
            request=response.request,
            status=response.status_code,
            exception=None
        )
    
    @staticmethod
    def from_exception(error: Exception, response: Optional[httpx.Response] = None) -> 'Result':
        """Crea Result desde excepción."""
        return Result(
            response=response,
            request=response.request if response else None,
            status=response.status_code if response else 0,
            exception=error
        )
    
    def on_status(
        self, 
        status_code: int, 
        handler: Callable[[httpx.Request, httpx.Response], None]
    ) -> 'Result':
        """Ejecuta handler si el status coincide. Retorna self para chaining.
        
        Ejemplo:
            result = await http.get("/users/1")
            result.on_status(404, lambda req, res: print("Not found"))
                  .on_status(200, lambda req, res: print("OK"))
                  .to(UserDTO)
        
        Args:
            status_code: Código HTTP a matchear
            handler: Función que recibe (request, response)
        
        Returns:
            self para permitir chaining
        """
        if self.status == status_code and self.response and self.request:
            handler(self.request, self.response)
        return self
    
    def on_exception(
        self, 
        handler: Callable[[Exception], None]
    ) -> 'Result':
        """Ejecuta handler si hubo excepción. Retorna self para chaining.
        
        Ejemplo:
            result = await http.get("/users/1")
            result.on_exception(lambda e: print(f"Error: {e}"))
                  .to(UserDTO)
        
        Args:
            handler: Función que recibe la excepción
        
        Returns:
            self para permitir chaining
        """
        if self.exception:
            handler(self.exception)
        return self
    
    def _is_optional_type(self, type_hint) -> bool:
        """Detecta si un type hint permite None (Optional o Union con None).
        
        Args:
            type_hint: Type hint a inspeccionar
        
        Returns:
            True si el type hint es Optional o Union que incluye None
        """
        origin = get_origin(type_hint)
        if origin is Union:
            args = get_args(type_hint)
            return type(None) in args
        return False
    
    def _validate_null_values(self, data: dict, target_type: Type[T]) -> list[str]:
        """Valida campos con None contra type hints no-opcionales.
        
        Args:
            data: Diccionario de datos a mapear
            target_type: Tipo destino con type hints
        
        Returns:
            Lista de nombres de campos con None que no son Optional
        """
        null_fields = []
        
        if is_dataclass(target_type):
            for field_info in fields(target_type):
                if field_info.name in data and data[field_info.name] is None:
                    if not self._is_optional_type(field_info.type):
                        null_fields.append(field_info.name)
        
        return null_fields
    
    def _map_response(self, response: httpx.Response, target_type: Type[T]) -> T:
        """Mapea httpx.Response a tipo especificado.
        
        Soporta:
        - Pydantic BaseModel
        - @dataclass
        - TypedDict
        - dict, list
        
        Args:
            response: Respuesta httpx
            target_type: Tipo destino para mapear
        
        Returns:
            Instancia del tipo mapeado
        
        Raises:
            ValueError: Si no puede parsear JSON
            TypeError: Si el tipo no es soportado
        """
        try:
            data = response.json()
        except Exception as e:
            raise ValueError(f"No se pudo parsear JSON de response: {e}")
        
        try:
            from pydantic import BaseModel
            if isinstance(target_type, type) and issubclass(target_type, BaseModel):
                return target_type.model_validate(data)
        except ImportError:
            pass
        
        if is_dataclass(target_type):
            field_names = {f.name for f in fields(target_type)}
            filtered_data = {k: v for k, v in data.items() if k in field_names}
            
            null_fields = self._validate_null_values(filtered_data, target_type)
            if null_fields:
                warnings.warn(
                    f"Fields {null_fields} have None values but are not typed as Optional in {target_type.__name__}",
                    UserWarning,
                    stacklevel=4
                )
            
            return target_type(**filtered_data)
        
        if target_type == dict or hasattr(target_type, '__annotations__'):
            return data  # type: ignore
        
        if target_type == list:
            if isinstance(data, list):
                return data  # type: ignore
            raise TypeError(f"Response data no es lista: {type(data)}")
        
        return data  # type: ignore
    
    def to(self, target_type: Type[T]) -> Optional[T]:
        """Proyecta respuesta al tipo especificado.
        
        Soporta:
        - Pydantic BaseModel (valida automáticamente con model_validate)
        - @dataclass (con validación de None en campos no-opcionales)
        - TypedDict
        - dict, list, etc.
        
        Para @dataclass, si un campo con valor None no está tipificado como Optional,
        se emitirá un UserWarning indicando la inconsistencia, pero el mapeo continuará.
        
        Ejemplo:
            user = (await http.get("/users/1")).to(UserDTO)
            
            # Si UserDTO.name no es Optional y el JSON tiene name: null,
            # emitirá warning pero mapeará el objeto de todas formas
        
        Returns:
            Instancia del tipo si response existe y mapeo exitoso, None si falla
        """
        if self.exception or not self.response:
            return None
        
        try:
            return self._map_response(self.response, target_type)
        except Exception:
            return None
