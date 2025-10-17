from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class FunctionTool:

    name: str
    """The name of the function tool"""

    description: str
    """The description of the function tool"""

    params_json_schema: dict[str, Any]
    """The JSON schema of the parameters of the function tool"""

    on_invoke_tool: Callable[..., Any]
    """The function to call when the tool is invoked"""