from agent.service import AgentService


class PatchedAgentService(AgentService):
    async def reset(self) -> None:
        super().reset()
        interpreter.reset()


if __name__ == "__main__":
    import logging
    import sys

    import uvicorn
    from fastapi import FastAPI
    from llama_index.agent.openai import OpenAIAgent
    from llama_index.llms.openai import OpenAI

    from agent.code_interpreter import CodeInterpreter, Function
    from environment.client import EnvClient

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

    client = EnvClient(host="localhost", port=8000, prefix="/env")

    functions = [
        Function(
            fn=client.action_to_callable(info),
            name=info.name,
            docstring=info.description,
            signature=info.signature,
        )
        for info in client.get_action_infos()
    ]

    interpreter = CodeInterpreter(functions)

    SYSTEM_PROMPT = """You are a helpful agent that deals with user requests.

    ## Pre-Defined Functions
    The interpreter environment is initialized with a set of pre-defined functions that you can use out of the box. If a pre-defined function can help solve the task, call it directly without redefining it.
    ```python
    {function_descriptions}
    ```
    """  # noqa: E501

    # Create the Agent with load/search tools
    agent = OpenAIAgent.from_tools(
        llm=OpenAI(model="gpt-4o"),
        tools=[interpreter.to_tool()],
        system_prompt=SYSTEM_PROMPT.format(
            function_descriptions=interpreter.get_function_descriptions()
        ),
        # verbose=True,
    )

    app = FastAPI()
    app.include_router(AgentService(agent))

    uvicorn.run(app, host="127.0.0.1", port=8001, reload=False, workers=1)
