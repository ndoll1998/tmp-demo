import inspect
from logging import getLogger
from typing import Any, Callable, ParamSpec, TypeVar
from uuid import uuid4

from fastapi.routing import APIRoute, APIRouter

from .dto import ActionArgs, ActionId, ActionInfo, ActionResult, Const

logger = getLogger(__name__)


class RemoteEnv(APIRouter):
    def __init__(self, prefix: str = "") -> None:
        self._registered_consts: list[Const] = []
        self._registered_action_infos: dict[ActionId, ActionInfo] = {}
        self._registered_action_fn: dict[ActionId, Callable] = {}

        routes = [
            # consts
            APIRoute(path="/consts", endpoint=self.get_consts, methods=["GET"]),
            # actions
            APIRoute(path="/action/ids", endpoint=self.get_action_ids, methods=["GET"]),
            APIRoute(path="/action/info", endpoint=self.get_action_info, methods=["GET"]),
            APIRoute(path="/action/take", endpoint=self.take_action, methods=["POST"]),
        ]

        super(RemoteEnv, self).__init__(
            prefix=prefix,
            routes=routes,
        )

    def get_consts(self) -> list[Const]:
        return self._registered_consts

    def get_action_ids(self) -> list[ActionId]:
        return list(self._registered_action_infos.keys())

    def get_action_info(self, action_id: ActionId):
        if action_id not in self._registered_action_infos:
            raise RuntimeError(f"Action id '{action_id}' invalid!")

        return self._registered_action_infos[action_id]

    def take_action(self, action_id: ActionId, args: ActionArgs) -> ActionResult:
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
            signature=str(inspect.signature(fn)),
        )

        self._registered_action_infos[action_id] = info
        self._registered_action_fn[action_id] = fn

        logger.info(f"Registered Action '{fn.__name__}' with action id '{action_id}'")

        return fn

    def register_const(self, name: str, value: Any, description: str) -> None:
        const = Const(
            name=name,
            value=value,
            description=description,
        )

        self._registered_consts.append(const)

        logger.info(f"Registered Constant '{name}={value}'")
