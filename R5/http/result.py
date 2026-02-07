from dataclasses import dataclass, fields, is_dataclass
from typing import Callable, Optional, Type, TypeVar, Union, get_args, get_origin

import httpx

from R5._utils import get_logger

T = TypeVar("T")
_logger = get_logger(__name__)


@dataclass
class Result:
    """Wrapper para respuestas HTTP con handlers encadenados y mapeo a tipos."""

    response: Optional[httpx.Response] = None
    request: Optional[httpx.Request] = None
    status: int = 0
    exception: Optional[Exception] = None

    @staticmethod
    def from_response(response: httpx.Response) -> "Result":
        return Result(
            response=response,
            request=response.request,
            status=response.status_code,
            exception=None,
        )

    @staticmethod
    def from_exception(
        error: Exception, response: Optional[httpx.Response] = None
    ) -> "Result":
        return Result(
            response=response,
            request=response.request if response else None,
            status=response.status_code if response else 0,
            exception=error,
        )

    def on_status(
        self, status_code: int, handler: Callable[[httpx.Request, httpx.Response], None]
    ) -> "Result":
        if self.status == status_code and self.response and self.request:
            handler(self.request, self.response)
        return self

    def on_exception(self, handler: Callable[[Exception], None]) -> "Result":
        if self.exception:
            handler(self.exception)
        return self

    def _is_optional_type(self, type_hint) -> bool:
        origin = get_origin(type_hint)
        if origin is Union:
            args = get_args(type_hint)
            return type(None) in args
        return False

    def _validate_null_values(self, data: dict, target_type: Type[T]) -> list[str]:
        null_fields = []
        if is_dataclass(target_type):
            for field_info in fields(target_type):
                if field_info.name in data and data[field_info.name] is None:
                    if not self._is_optional_type(field_info.type):
                        null_fields.append(field_info.name)
        return null_fields

    def _map_response(self, response: httpx.Response, target_type: Type[T]) -> T:
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
                _logger.warning(
                    f"Fields {null_fields} have None values but are not typed as Optional in {target_type.__name__}"
                )

            return target_type(**filtered_data)

        if target_type == dict or hasattr(target_type, "__annotations__"):
            return data  # type: ignore

        if target_type == list:
            if isinstance(data, list):
                return data  # type: ignore
            raise TypeError(f"Response data no es lista: {type(data)}")

        return data  # type: ignore

    def to(self, target_type: Type[T]) -> Optional[T]:
        if self.exception or not self.response:
            return None
        try:
            return self._map_response(self.response, target_type)
        except Exception as e:
            _logger.warning(
                f"Failed to map response to {target_type.__name__}: {e}",
                exc_info=True
            )
            return None
