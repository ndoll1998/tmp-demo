#!/usr/bin/env python


if __name__ == "__main__":
    import asyncio

    from agent.callbacks import LoggingCallback
    from environment.client import EnvClient
    from utils.callbacks import NotebookCallbackWithEnv
    from utils.logging import setup_logging
    from utils.ws import connect_and_receive_messages

    setup_logging()

    env_client = EnvClient(host="localhost", port=8001, prefix="/env")
    std_env_client = EnvClient(host="localhost", port=8002, prefix="/env")

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
