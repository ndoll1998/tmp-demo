import inspect
from uuid import uuid4
from logging import getLogger
from typing import Any, ParamSpec, TypeVar, Callable

from pydantic import BaseModel
from fastapi import Body
from fastapi.routing import APIRouter, APIRoute

from .interface import ActionId, ActionInfo

class Args(BaseModel):
    args: tuple[Any] = ()
    kwargs: dict[str, Any] = {}

class Result(BaseModel):
    result: Any

logger = getLogger(__name__)

class RemoteEnv(APIRouter):

    def __init__(self, prefix: str = "") -> None:

        self._registered_action_infos: dict[ActionId, ActionInfo] = {}
        self._registered_action_fn: dict[ActionId, Callable] = {}

        routes = [
            APIRoute(path="/action/ids", endpoint=self.get_action_ids, methods=["GET"]),
            APIRoute(path="/action/info", endpoint=self.get_action_info, methods=["GET"]),
            APIRoute(path="/action/take", endpoint=self.take_action, methods=["POST"])
        ]

        super(RemoteEnv, self).__init__(
            prefix=prefix,
            routes=routes,
        )

    def get_action_ids(self) -> list[ActionId]:
        return list(self._registered_action_infos.keys())

    def get_action_info(self, action_id: ActionId):

        if action_id not in self._registered_action_infos:
            raise RuntimeError(f"Action id '{action_id}' invalid!")

        return self._registered_action_infos[action_id]

    def take_action(self, action_id: ActionId, args: Args = Body(...)) -> Result:

        if action_id not in self._registered_action_infos:
            raise RuntimeError(f"Action id '{action_id}' invalid!")

        fn = self._registered_action_fn[action_id]
        result = fn(*args.args, **args.kwargs)

        return {"result": result}


    P = ParamSpec("P")
    R = TypeVar("T")

    def register_action(self, fn: Callable[P, R]) -> Callable[P, R]:

        action_id = str(uuid4())

        info = ActionInfo(
            action_id=action_id,
            name=fn.__name__,
            description=fn.__doc__,
            signature=str(inspect.signature(fn))
        )

        self._registered_action_infos[action_id] = info
        self._registered_action_fn[action_id] = fn

        logger.info(f"Registered Action '{fn.__name__}' with action id '{action_id}'")

        return fn
