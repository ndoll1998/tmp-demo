"""Data Transfer Objects"""

from typing import Annotated, Any, TypeAlias

from PIL import Image
from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer

from environment.utils import base64_to_pil_image, pil_image_to_base64

ActionId: TypeAlias = str


class ActionInfo(BaseModel):
    action_id: str
    name: str
    description: str
    signature: str


def deserialize_base64(str_base64: str, dtype: str) -> Any:
    if dtype == "PIL.Image.Image":
        return base64_to_pil_image(str_base64)
    else:
        raise NotImplementedError()


def validate(obj: Any):
    if isinstance(obj, dict):
        if "type" in obj and "str_base64" in obj:
            return deserialize_base64(obj["str_base64"], obj["type"])
        else:
            return {k: validate(v) for k, v in obj.items()}
    elif isinstance(obj, tuple):
        return tuple(validate(v) for v in obj)
    elif isinstance(obj, list):
        return [validate(v) for v in obj]
    else:
        return obj


def serialize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    elif isinstance(obj, tuple):
        return tuple(serialize(v) for v in obj)
    elif isinstance(obj, list):
        return [serialize(v) for v in obj]
    elif isinstance(obj, Image.Image):
        return {
            "type": "PIL.Image.Image",
            "str_base64": pil_image_to_base64(obj),
        }
    else:
        return obj


class ActionArgs(BaseModel):
    args: list[Annotated[Any, BeforeValidator(validate), PlainSerializer(serialize)]] = Field(
        default_factory=list
    )
    kwargs: dict[
        str, Annotated[Any, BeforeValidator(validate), PlainSerializer(serialize)]
    ] = Field(default_factory=dict)


class ActionResult(BaseModel):
    result: Annotated[Any, BeforeValidator(validate), PlainSerializer(serialize)]


class Const(BaseModel):
    name: str
    value: Annotated[Any, BeforeValidator(validate), PlainSerializer(serialize)]
    description: str
