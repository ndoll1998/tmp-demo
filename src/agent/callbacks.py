import json
import logging

import nbformat as nbf

from agent.dto import ChatMessage, MessageRole


class AgentCallback:
    def on_step(self, chat_message: ChatMessage) -> None:
        ...


class NotebookCallback(AgentCallback):
    def __init__(
        self,
        file_path: str,
        interpreter_tool_name: str = "python",
        interpreter_argument_name: str = "code",
        msg_format_str: str = "**{role}**: {message}",
    ) -> None:
        self.file_path = file_path
        self.interpreter_argument_name = interpreter_argument_name
        self.interpreter_tool_name = interpreter_tool_name
        self.msg_format_str = msg_format_str
        self.nb = nbf.v4.new_notebook()

    def on_step(self, chat_message: ChatMessage) -> None:
        if chat_message.content is not None and chat_message.role != MessageRole.TOOL:
            cell = nbf.v4.new_markdown_cell(
                self.msg_format_str.format(
                    role=chat_message.role.value, message=chat_message.content
                )
            )
            self.add_cells(cell)

        if chat_message.role == MessageRole.ASSISTANT:
            if "tool_calls" in chat_message.additional_kwargs:
                for tool_call in chat_message.additional_kwargs["tool_calls"]:
                    if tool_call["function"]["name"] == self.interpreter_tool_name:
                        args = json.loads(tool_call["function"]["arguments"])
                        cell = nbf.v4.new_code_cell(args[self.interpreter_argument_name])
                        self.add_cells(cell)
                    else:
                        pass
                        # raise NotImplementedError()

        elif chat_message.role == MessageRole.TOOL:
            self.add_cell_output(chat_message.content.strip())

    def add_cells(self, *cells: nbf.NotebookNode) -> None:
        self.nb["cells"].extend(cells)
        self.write()

    def add_cell_output(self, output: str, index: int = -1) -> None:
        cell: nbf.NotebookNode = self.nb["cells"][index]
        cell.setdefault("outputs", [])
        cell["outputs"].append(
            nbf.v4.new_output(
                output_type="execute_result", execution_count=1, data={"text/plain": output}
            )
        )
        self.write()

    def write(self) -> None:
        with open(self.file_path, "w") as fp:
            nbf.write(self.nb, fp)


class LoggingCallback(AgentCallback):
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def on_step(self, chat_message: ChatMessage) -> None:
        if chat_message.content is not None and chat_message.role != MessageRole.TOOL:
            self.logger.info(f"{chat_message.role.value}: {chat_message.content}")

        if chat_message.role == MessageRole.ASSISTANT:
            if "tool_calls" in chat_message.additional_kwargs:
                for tool_call in chat_message.additional_kwargs["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    arguments = format_to_kwargs(tool_call["function"]["arguments"])
                    self.logger.info(f"{chat_message.role.value}: {tool_name}(\n{arguments}\n)")

        elif chat_message.role == MessageRole.TOOL:
            tool_name = chat_message.additional_kwargs["name"]
            self.logger.info(f"TOOL[{tool_name}]: {chat_message.content}")


def format_to_kwargs(args: str) -> str:
    d = json.loads(args)

    formatted_kwargs = []
    backslash_char = "\\"

    for key, value in d.items():
        # Check if the value is a multiline string
        if isinstance(value, str) and "\n" in value:
            # Format multiline strings with triple backticks and further indentation
            formatted_value = f"```{backslash_char}n        {value.replace('{backslash_char}n', '{backslash_char}n        ')}{backslash_char}n    ```"
        else:
            # Use repr for single-line values and add normal indentation
            formatted_value = repr(value)

        # Format each key-value pair as a keyword argument with initial indentation
        formatted_kwargs.append(f"    {key}={formatted_value}")

    # Join each argument on a new line
    return "\n".join(formatted_kwargs)
