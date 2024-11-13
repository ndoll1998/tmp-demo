"""Data Transfer Objects"""

from typing import TypeAlias
from pydantic import BaseModel

ActionId: TypeAlias = str

class ActionInfo(BaseModel):
    action_id: str
    name: str
    description: str
    signature: str
