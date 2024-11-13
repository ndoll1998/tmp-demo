import inspect
import io
import logging
import sys
from dataclasses import dataclass
from typing import Callable

from IPython.terminal.interactiveshell import TerminalInteractiveShell
from llama_index.core.tools import FunctionTool

logger = logging.getLogger(__name__)


@dataclass
class Function:
    name: str
    signature: str
    docstring: str
    fn: callable

    @classmethod
    def from_defaults(
        cls,
        fn: Callable,
        name: str | None = None,
        docstring: str | None = None,
        signature: str | None = None,
    ) -> "Function":
        return Function(
            name=name or fn.__name__,
            signature=signature or str(inspect.signature(fn)),
            docstring=docstring or fn.__doc__,
            fn=fn,
        )


@dataclass
class CodeCell:
    input: str
    output: str


CODE_INTERPRETER_PROMPT = """## Python Interpreter
You have access to a code interpreter tool, `python`, where you can execute Python code in a Jupyter-like environment. This environment has persistent memory, meaning all variables, functions, and objects that you define will remain available for subsequent calls to the `python` interpreter. **Use previously defined variables and results directly when they are relevant to a task.**

### Code Writing Guidelines
- **Write clean, readable code**: Use comments to explain what each part of the code does.
- **Reuse Existing Variables**: When variables are created in previous steps, use them directly rather than recreating them. This reduces redundant code and ensures efficient use of the persistent environment.
- **Store Outputs as Variables**: When calling functions that return outputs needed later, store them in variables. This allows you to reference these variables in subsequent code without recomputation.
"""  # noqa: E501


class CodeInterpreter:
    def __init__(self, functions: list[Function] | None = None) -> None:
        self.history: list[CodeCell] = []
        self.functions = functions or []
        # Create an embedded IPython instance
        self.shell = self.create_shell()

    def run_cell(self, code: str) -> str:
        """Runs python code in a ipython cell and returns the captured stdout.

        Args:
            code (str): The code to run in the cells as one single string.

        Returns:
            (str): The output of the ipython cell including all captured stdout.
        """
        logger.info("------ Code ------\n" + code + "\n------------")
        # Create a StringIO buffer to capture output
        buffer = io.StringIO()
        # Redirect stdout to the buffer
        sys.stdout = buffer  # noqa: B018
        try:
            # Execute the code
            self.shell.run_cell(code)
        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__

        # Retrieve the captured output
        output = buffer.getvalue()
        buffer.close()

        self.history.append(CodeCell(input=code, output=output))

        return output

    def create_shell(self) -> TerminalInteractiveShell:
        shell = TerminalInteractiveShell.instance()
        for fn in self.functions:
            # Inject fn into the shell's user namespace
            shell.user_ns[fn.name] = fn.fn
        return shell

    def reset(self) -> None:
        del self.shell
        self.shell = self.create_shell()

    def to_tool(self) -> FunctionTool:
        return FunctionTool.from_defaults(
            fn=self.run_cell,
            name="python",
            description=CODE_INTERPRETER_PROMPT,
        )

    def get_history(self) -> str:
        return "\n\n".join(
            [
                f"In [{i}]: {cell.input}\nOut[{i}]: {cell.output}"
                for i, cell in enumerate(self.history)
            ]
        )

    def get_function_descriptions(self) -> str:
        return "\n\n".join(
            [
                f'def {fn.name}{fn.signature}\n    """{fn.docstring.strip()}\n    """\n'
                for fn in self.functions
            ]
        )
