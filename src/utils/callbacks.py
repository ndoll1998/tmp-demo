import nbformat as nbf

from agent.callbacks import NotebookCallback
from environment.client import EnvClient


class NotebookCallbackWithEnv(NotebookCallback):
    def __init__(
        self,
        file_path: str,
        env_client: EnvClient | None = None,
        std_env_client: EnvClient | None = None,
        interpreter_tool_name: str = "python",
        interpreter_argument_name: str = "code",
        msg_format_str: str = "**{role}**: {message}",
    ) -> None:
        super().__init__(
            file_path, interpreter_tool_name, interpreter_argument_name, msg_format_str
        )

        if env_client is not None:
            self.add_cells(self.code_cell_from_env(env_client))
        if std_env_client is not None:
            self.add_cells(self.code_cell_from_env(std_env_client))

    def code_cell_from_env(self, env_client: EnvClient) -> nbf.NotebookNode:
        code_lines = (
            [
                "from environment.client import EnvClient",
                f"client = EnvClient(host='{env_client.host}', port={env_client.port}, prefix='{env_client.prefix}')",  # noqa: E501
            ]
            + [
                f"{info.name} = client.action_to_callable(client.get_action_info_from_name('{info.name}'))"  # noqa: E501
                for info in env_client.get_action_infos()
            ]
            + [
                f"{name} = client.consts['{const.name}'].value"
                for name, const in env_client.consts.items()
            ]
        )

        code = "\n".join(code_lines)
        return nbf.v4.new_code_cell(code)
