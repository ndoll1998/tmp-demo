from agent.service import AgentService


class PatchedAgentService(AgentService):
    async def reset(self) -> None:
        super().reset()
        interpreter.reset()


SYSTEM_PROMPT = """You are a helpful agent that deals with user requests.

## Python Interpreter
You have access to a code interpreter tool, `python`, where you can execute Python code in a Jupyter-like environment. This environment has persistent memory, meaning all variables, functions, and objects that you define will remain available for subsequent calls to the `python` interpreter.

### Pre-Defined Functions
The interpreter environment is initialized with a set of pre-defined functions that you can use out of the box. If a pre-defined function can help solve the task, call it directly without redefining it.
```python
{function_descriptions}
```

### Pre-Defined variables
The interpreter environment is also initialized with a set of pre-defined variables that can be used out of the box. If a pre-defined variable can help solve the task, use it directly without redefining it.
```
{constant_descriptions}
```

CAUTION: The pre-defined functions and variables are only available inside the interpreter and must not be called via the function calling API.

### Code Writing Guidelines
- **Write clean, readable code**: Use comments to explain what each part of the code does.
- **Reuse Existing Variables**: When variables are created in previous steps, use them directly rather than recreating them. This reduces redundant code and ensures efficient use of the persistent environment.
- **Store Outputs as Variables**: When calling functions that return outputs needed later, store them in variables. This allows you to reference these variables in subsequent code without recomputation.
- **Avoid Hard-Coding**: Do not hard-code specific values; instead, use variables and write code that is generic and reusable. This ensures flexibility and adaptability in different contexts.
"""  # noqa: E501


if __name__ == "__main__":
    import logging
    import sys

    import uvicorn
    from fastapi import FastAPI
    from llama_index.agent.openai import OpenAIAgent
    from llama_index.llms.openai import OpenAI

    from agent.code_interpreter import CodeInterpreter, Constant, Function
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

    constants = [
        Constant.from_defaults(
            name="conveyer_belt_x",
            docstring="The X-Coordinates of the left and right boundary of the conveyer belt.",
            value=(0, 20),
        ),
        Constant.from_defaults(
            name="conveyer_belt_y",
            docstring="The Y-Coordinates of the upper and lower boundary of the conveyer belt.",
            value=(0, 100),
        ),
        Constant.from_defaults(
            name="conveyer_belt_z",
            docstring="The Z-Coordinate that indicates the height of the conveyer belt.",
            value=10,
        ),
    ]

    interpreter = CodeInterpreter(constants=constants, functions=functions)

    # Create the Agent with load/search tools
    agent = OpenAIAgent.from_tools(
        llm=OpenAI(model="gpt-4o"),
        tools=[interpreter.to_tool()],
        system_prompt=SYSTEM_PROMPT.format(
            function_descriptions=interpreter.get_function_descriptions(),
            constant_descriptions=interpreter.get_constant_descriptions(),
        ),
        verbose=True,
    )

    app = FastAPI()
    app.include_router(AgentService(agent))

    uvicorn.run(app, host="127.0.0.1", port=8001, reload=False, workers=1)
