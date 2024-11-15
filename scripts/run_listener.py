#!/usr/bin/env python


if __name__ == "__main__":
    import asyncio

    import httpx

    from agent.callbacks import LoggingCallback
    from environment.client import EnvClient
    from utils.callbacks import NotebookCallbackWithEnv
    from utils.constants import (
        AGENT_HOST_ADRESS,
        AGENT_PORT,
        ENV_HOST_ADRESS,
        ENV_PORT,
        STD_ENV_HOST_ADRESS,
        STD_ENV_PORT,
    )
    from utils.logging import setup_logging
    from utils.ws import connect_and_receive_messages

    setup_logging()

    # reset agent
    httpx.get(f"http://{AGENT_HOST_ADRESS}:{AGENT_PORT}/reset")

    env_client = EnvClient(host=ENV_HOST_ADRESS, port=ENV_PORT)
    std_env_client = EnvClient(host=STD_ENV_HOST_ADRESS, port=STD_ENV_PORT)

    callbacks = [
        LoggingCallback(),
        NotebookCallbackWithEnv(
            file_path="output/notebook.ipynb",
            env_client=env_client if env_client.healthy else None,
            std_env_client=std_env_client if std_env_client.healthy else None,
        ),
    ]

    while True:
        asyncio.run(connect_and_receive_messages(callbacks=callbacks))
