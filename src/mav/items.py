from pydantic import BaseModel
from typing import MutableMapping, Mapping

class FunctionCall(BaseModel):
    """An object containing information about a function call requested by an agent."""

    function: str
    """The name of the function to call."""
    args: MutableMapping[str, "FunctionCallArgTypes"]
    """The arguments to pass to the function."""
    id: str | None = None
    """An optional ID for the function call. E.g., used by OpenAI and Anthropic."""
    placeholder_args: Mapping[str, "FunctionCallArgTypes"] | None = None
    """An optional dictionary of placeholder arguments to use in by ground truth agent in injection tasks."""


FunctionCallArgTypes = str | int | float | bool | None | dict | list | FunctionCall
"""Valid types for function call arguments."""
