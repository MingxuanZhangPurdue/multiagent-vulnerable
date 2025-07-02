import inspect
from typing import Callable, Any
from mav.Tasks.base_environment import TaskEnvironment

try:
    import agents
    from agents import RunContextWrapper, function_tool, FunctionTool
except ImportError:
    agents = None

def convert_to_openai_function_tool(func: Callable[..., Any]) -> FunctionTool:

    """
    Helper function to convert a regular function into an OpenAI FunctionTool.
    """
    if agents is None:
        raise ImportError("OpenAI Agents module is not available.")
    
    # Get original function signature
    sig = inspect.signature(func)

    # Create new parameters list, replacing first parameter type
    new_params = []
    
    for i, (name, param) in enumerate(sig.parameters.items()):
        if issubclass(param.annotation, TaskEnvironment):
            # Replace with RunContextWrapper type
            new_param = param.replace(annotation=RunContextWrapper[param.annotation])
        else:
            new_param = param
        new_params.append(new_param)
    
    # Create new signature
    new_sig = sig.replace(parameters=new_params)
    
    
    def wrapper(*args, **kwargs):
        # Convert first argument from RunContextWrapper to actual environment
        if args:
            environment_wrapper = args[0]
            actual_environment = environment_wrapper.context
            new_args = (actual_environment,) + args[1:]
            return func(*new_args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    # Apply the new signature to the wrapper
    wrapper.__signature__ = new_sig
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    
    return function_tool()(wrapper)