import base64
import os
from logging import getLogger

from llama_index.core.agent import ReActAgent
from llama_index.core.prompts import PromptTemplate
from llama_index.llms.openai_like import OpenAILike

from agent.code_interpreter import CodeInterpreter, Constant, Function
from agent.service import AgentService
from environment.client import EnvClient
from utils.constants import ENV_HOST_ADRESS, ENV_PORT, STD_ENV_HOST_ADRESS, STD_ENV_PORT
from utils.logging import setup_logging

setup_logging()
logger = getLogger(__name__)


class PatchedAgentService(AgentService):
    async def reset(self) -> None:
        super().reset()
        interpreter.reset()


SYSTEM_PROMPT = """You are an multilingual agent that controls a robot arm.{environment_description}

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

## Modality
You capabilities are limited to textual understanding. Make use of the pre-defined functions inside the code interpreter to interpret other modalities, e.g. images, in code.
"""  # noqa: E501

constants = []
functions = []

# get functions and constants from the robot environment
env_client = EnvClient(host=ENV_HOST_ADRESS, port=ENV_PORT)
if env_client.healthy:
    for info in env_client.get_action_infos():
        logger.info(f"Got function {info.name}{info.signature}")
        functions.append(
            Function(
                fn=env_client.action_to_callable(info),
                name=info.name,
                docstring=info.description,
                signature=info.signature,
            )
        )

    for const in env_client.consts.values():
        logger.info(f"Got constant {const.name}={const.value}")
        constants.append(
            Constant.from_defaults(
                name=const.name,
                docstring=const.description,
                value=const.value,
            )
        )

# get functions and constants from the std environment
std_env_client = EnvClient(host=STD_ENV_HOST_ADRESS, port=STD_ENV_PORT)
if std_env_client.healthy:
    for info in std_env_client.get_action_infos():
        logger.info(f"Got function {info.name}{info.signature}")
        functions.append(
            Function(
                fn=std_env_client.action_to_callable(info),
                name=info.name,
                docstring=info.description,
                signature=info.signature,
            )
        )

    for const in std_env_client.consts.values():
        logger.info(f"Got constant {const.name}={const.value}")
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
    # environment_description=(
    #     f"\n\n{env_client.env_description}" if env_client.env_description != "" else ""
    # ),
    environment_description="",
    function_descriptions=interpreter.get_function_descriptions(),
    constant_descriptions=interpreter.get_constant_descriptions(),
)

# # OpenAI
# from llama_index.llms.openai import OpenAI
# from llama_index.agent.openai import OpenAIAgent

# agent = OpenAIAgent.from_tools(
#     llm=OpenAI(model="gpt-4o"),
#     tools=[interpreter.to_tool()],
#     system_prompt=SYSTEM_PROMPT,
#     max_function_calls=50
#     # verbose=True,
# )


# GenAI Platform

username = os.environ["GENAI_USERNAME"]
password = os.environ["GENAI_PASSWORD"]
token_string = f"{username}:{password}"
token_bytes = base64.b64encode(token_string.encode())

llm = OpenAILike(
    model="Llama-3.1-70B-Instruct",
    is_chat_model=True,
    api_key="xxxx",
    api_base="https://genai.iais.fraunhofer.de/api/v2",
    default_headers={"Authorization": f"Basic {token_bytes.decode()}"},
)
print("DEFAULT_HEADERS", llm.default_headers)
agent = ReActAgent.from_tools(
    llm=llm,
    tools=[interpreter.to_tool()],
    # verbose=True,
)
react_system_prompt = agent.get_prompts()["agent_worker:system_prompt"]
agent.update_prompts(
    {
        "agent_worker:system_prompt": PromptTemplate(
            react_system_prompt.template + "\n" + SYSTEM_PROMPT
        )
    }
)


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from utils.constants import AGENT_HOST_ADRESS, AGENT_PORT

    app = FastAPI()
    app.include_router(AgentService(agent))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Origins allowed to access the API
        allow_credentials=True,  # Allow cookies and credentials
        allow_methods=["*"],  # Allow all HTTP methods (GET, POST, OPTIONS, etc.)
        allow_headers=["*"],  # Allow all headers (e.g., Content-Type, Authorization)
    )

    uvicorn.run(app, host=AGENT_HOST_ADRESS, port=AGENT_PORT, reload=False, workers=1)
