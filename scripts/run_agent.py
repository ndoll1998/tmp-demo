import logging
import sys

from llama_index.agent.openai import OpenAIAgent
from llama_index.llms.openai import OpenAI

from agent.code_interpreter import CodeInterpreter, Constant, Function
from agent.service import AgentService
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


class PatchedAgentService(AgentService):
    async def reset(self) -> None:
        super().reset()
        interpreter.reset()


SYSTEM_PROMPT = """You are an agent that controls a robot arm.{environment_description}

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

constants = []
functions = []

# get functions and constants from the robot environment
env_client = EnvClient(host="localhost", port=8001, prefix="/env")
if env_client.healthy:
    for info in env_client.get_action_infos():
        functions.append(
            Function(
                fn=env_client.action_to_callable(info),
                name=info.name,
                docstring=info.description,
                signature=info.signature,
            )
        )

    for const in env_client.consts.values():
        constants.append(
            Constant.from_defaults(
                name=const.name,
                docstring=const.description,
                value=const.value,
            )
        )

# get functions and constants from the std environment
std_env_client = EnvClient(host="localhost", port=8002, prefix="/env")
if std_env_client.healthy:
    for info in std_env_client.get_action_infos():
        functions.append(
            Function(
                fn=std_env_client.action_to_callable(info),
                name=info.name,
                docstring=info.description,
                signature=info.signature,
            )
        )

    for const in std_env_client.consts.values():
        constants.append(
            Constant.from_defaults(
                name=const.name,
                docstring=const.description,
                value=const.value,
            )
        )

# create the code interpreter tool
interpreter = CodeInterpreter(constants=constants, functions=functions)

# format the system prompt
SYSTEM_PROMPT = SYSTEM_PROMPT.format(
    environment_description=(
        f"\n\n{env_client.env_description}" if env_client.env_description != "" else ""
    ),
    function_descriptions=interpreter.get_function_descriptions(),
    constant_descriptions=interpreter.get_constant_descriptions(),
)

# Create the Agent with load/search tools
agent = OpenAIAgent.from_tools(
    llm=OpenAI(model="gpt-4o"),
    tools=[interpreter.to_tool()],
    system_prompt=SYSTEM_PROMPT,
    # verbose=True,
)


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(AgentService(agent))

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False, workers=1)
