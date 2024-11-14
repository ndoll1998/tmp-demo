"""Data Transfer Objects"""

from typing import Any, TypeAlias

from pydantic import BaseModel, Field

ActionId: TypeAlias = str


class ActionInfo(BaseModel):
    action_id: str
    name: str
    description: str
    signature: str


class ActionArgs(BaseModel):
    args: list[Any] = Field(default_factory=list)
    kwargs: dict[str, Any] = Field(default_factory=dict)


class ActionResult(BaseModel):
    result: Any


class Const(BaseModel):
    name: str
    value: Any
    description: str

