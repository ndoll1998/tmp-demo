import asyncio

import httpx
import nbformat as nbf
import websockets

from agent.callbacks import AgentCallback, NotebookCallback
from agent.dto import ChatMessage, MessageRole
from environment.client import EnvClient


class NotebookCallbackWithEnv(NotebookCallback):
    def __init__(
        self,
        env_client: EnvClient,
        file_path: str,
        interpreter_tool_name: str = "python",
        interpreter_argument_name: str = "code",
        msg_format_str: str = "**{role}**: {message}",
    ) -> None:
        super().__init__(
            file_path, interpreter_tool_name, interpreter_argument_name, msg_format_str
        )

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
        self.add_cells(nbf.v4.new_code_cell(code))


async def connect_and_receive_messages(
    message: str,
    host: str = "localhost",
    port: int = 8001,
    callbacks: list[AgentCallback] = [],
) -> str:
    client = httpx.AsyncClient(base_url=f"http://{host}:{port}", timeout=None)

    for cb in callbacks:
        cb.on_start(ChatMessage(role=MessageRole.USER, content=message))

    async with websockets.connect(f"ws://{host}:{port}/ws/steps") as websocket:
        coro = client.post("/chat", params={"message": message})
        task = asyncio.create_task(coro)

        try:
            # Continuously listen for messages from the server
            async for data in websocket:
                chat_message = ChatMessage.model_validate_json(data)
                for cb in callbacks:
                    cb.on_step(chat_message)

        except websockets.ConnectionClosed:
            print("WebSocket connection closed")

        response = await task
        for cb in callbacks:
            cb.on_completion(response.text)

    return response


if __name__ == "__main__":
    import logging.config
    import sys

    from agent.callbacks import LoggingCallback

    # Define basic configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "standard",
                "level": "INFO",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
    }

    # Apply the configuration
    logging.config.dictConfig(logging_config)

    # reset agent
    httpx.get("http://localhost:8001/reset")

    env_client = EnvClient(host="localhost", port=8000, prefix="/env")

    callbacks = [
        LoggingCallback(),
        NotebookCallbackWithEnv(env_client, "output/notebook.ipynb"),
    ]

    while (user_input := input("USER: ")) != "":
        # Run the WebSocket client
        asyncio.run(connect_and_receive_messages(user_input, callbacks=callbacks))
