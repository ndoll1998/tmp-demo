from functools import cache, cached_property, partial
from typing import Any, Callable

import httpx

from environment.dto import ActionArgs, ActionId, ActionInfo, ActionResult, Const


class EnvClient(object):
    def __init__(self, host: str, port: int, protocol: str = "http", prefix: str = "") -> None:
        self.host = host
        self.port = port
        self.protocol = protocol
        self.prefix = prefix

    @property
    def base_url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}{self.prefix}"

    @cached_property
    def consts(self) -> list[Const]:
        return httpx.get(f"{self.base_url}/consts").json()

    @cache
    def get_action_ids(self) -> list[ActionId]:
        return httpx.get(f"{self.base_url}/action/ids").json()

    @cache
    def get_action_infos(self) -> list[ActionInfo]:
        action_infos = []
        for i in self.get_action_ids():
            response = httpx.get(f"{self.base_url}/action/info", params={"action_id": i})
            action_infos.append(ActionInfo.model_validate_json(response.content))
        return action_infos

    def take_action(self, info: ActionInfo, *args: Any, **kwargs: Any) -> Any:
        action_args = ActionArgs(args=args, kwargs=kwargs)
        response = httpx.post(
            url=f"{self.base_url}/action/take",
            params={"action_id": info.action_id},
            content=action_args.model_dump_json(),
        )
        action_result = ActionResult.model_validate_json(response.content)
        return action_result.result

    def action_to_callable(self, info: ActionInfo) -> Callable:
        return partial(self.take_action, info)

    def get_action_info_from_name(self, name: str) -> ActionInfo:
        for info in self.get_action_infos():
            if info.name == name:
                return info
        raise ValueError(name)

