from __future__ import annotations
import inspect
from dataclasses import dataclass
from typing import Any, Callable, get_type_hints
from docstring_parser import parse

from mav.Tasks.base_environment import TaskEnvironment

@dataclass
class FunctionTool:

    name: str
    """The name of the function tool"""

    description: str
    """The description of the function tool"""

    params_json_schema: dict[str, Any]
    """The JSON schema of the parameters of the function tool"""

    on_invoke_tool: Callable[..., str | FunctionToolCallResult]
    """The function to call when the tool is invoked, the function should return either a string or a FunctionToolCallResult."""

@dataclass
class FunctionToolCallResult:
    output: str | Any
    """The result returned by the function tool."""

    usage: dict[str, dict[str, Any]] | None = None
    """A dictionary containing usage statistics during the function tool call, since the function may involve model usage."""

    appendix: dict[str, Any] | None = None
    """An optional dictionary containing any additional information related to the function tool call."""

def _is_context_parameter(param: inspect.Parameter, func: Callable) -> bool:
    """Check if a parameter is a TaskEnvironment context parameter."""
    try:
        # Get type hints for the function
        type_hints = get_type_hints(func)
        param_type = type_hints.get(param.name)
        
        # Check if the parameter type is TaskEnvironment or a subclass
        if param_type and inspect.isclass(param_type):
            return issubclass(param_type, TaskEnvironment)
        
        return False
    except Exception:
        return False

def convert_to_function_tool(func: Callable[..., Any]) -> FunctionTool:
    """
    Helper function to convert a regular function into a FunctionTool
    by inspecting its signature and docstring.
    
    Automatically excludes TaskEnvironment context parameters from the schema.
    """
    # Extract the function name
    name = func.__name__

    # Extract the description and parsed docstring
    docstring = inspect.getdoc(func) or ""
    parsed_doc = parse(docstring) if docstring else None
    short_description = parsed_doc.short_description if parsed_doc else ""
    long_description = parsed_doc.long_description if parsed_doc else ""
    description = "\n\n".join(filter(None, [short_description, long_description]))
    doc_params = {p.arg_name: p for p in (parsed_doc.params if parsed_doc else [])}

    # Generate JSON schema for parameters
    sig = inspect.signature(func)
    parameters = sig.parameters

    type_mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }
    str_type_mapping = {
        "str": "string",
        "string": "string",
        "int": "integer",
        "integer": "integer",
        "float": "number",
        "double": "number",
        "number": "number",
        "bool": "boolean",
        "boolean": "boolean",
        "list": "array",
        "array": "array",
        "dict": "object",
        "dictionary": "object",
        "object": "object",
    }

    def resolve_json_type(annotation: Any, doc_param_type: str | None) -> str:
        if annotation in type_mapping:
            return type_mapping[annotation]
        if isinstance(annotation, type) and annotation in type_mapping:
            return type_mapping[annotation]
        if doc_param_type:
            return str_type_mapping.get(doc_param_type.lower(), "string")
        return "string"

    properties = {}
    required = []

    for param in parameters.values():
        if param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY):
            # Skip TaskEnvironment context parameters
            if _is_context_parameter(param, func):
                continue
            
            doc_param = doc_params.get(param.name)
            property_schema = {
                "type": resolve_json_type(param.annotation, getattr(doc_param, "type_name", None)),
            }
            if doc_param and doc_param.description:
                property_schema["description"] = doc_param.description.strip()

            properties[param.name] = property_schema

            if param.default is inspect.Parameter.empty:
                required.append(param.name)

    params_json_schema = {
        "type": "object",
        "properties": properties,
    }
    if required:
        params_json_schema["required"] = required

    # Create and return the FunctionTool instance
    return FunctionTool(
        name=name,
        description=description,
        params_json_schema=params_json_schema,
        on_invoke_tool=func,
    )