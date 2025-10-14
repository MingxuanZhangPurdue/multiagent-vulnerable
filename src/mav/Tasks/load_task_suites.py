import importlib
from pathlib import Path
from collections import defaultdict
from mav.Tasks.task_suite import TaskSuite


def _discover_task_suites() -> dict[str, TaskSuite]:
    """
    Automatically discover and load all task suites.
    
    Scans all subdirectories under mav.Tasks, finds modules containing task_suite.py,
    and automatically imports TaskSuite instances from them.
    
    Returns:
        dict[str, TaskSuite]: Dictionary with suite names as keys and TaskSuite instances as values
    """
    suites = {}
    
    # Get the Tasks directory path
    tasks_dir = Path(__file__).parent
    
    # Iterate through all subdirectories in the Tasks directory
    for item in tasks_dir.iterdir():
        # Skip non-directories, private directories, and utility directories
        if not item.is_dir() or item.name.startswith('_') or item.name == 'utils':
            continue
        
        # Check if task_suite.py file exists
        task_suite_file = item / 'task_suite.py'
        if not task_suite_file.exists():
            continue
        

        print("Loading task suite from:", item.name)
        try:
            # Dynamically import the module
            module_name = f"mav.Tasks.{item.name}.task_suite"
            module = importlib.import_module(module_name)
            
            # Look for TaskSuite instance in the module
            # Usually named as {dir_name}_task_suite
            suite_var_name = f"{item.name}_task_suite"
            
            if hasattr(module, suite_var_name):
                suite = getattr(module, suite_var_name)
                if isinstance(suite, TaskSuite):
                    suites[suite.name] = suite
            else:
                # If standard naming not found, try to find any TaskSuite instance
                for attr_name in dir(module):
                    if not attr_name.startswith('_'):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, TaskSuite):
                            suites[attr.name] = attr
                            break
        except Exception as e:
            # If import fails, skip this module and continue
            print(f"Warning: Failed to load task suite from {item.name}: {e}")
            continue
    
    return suites


# Automatically discover and load all task suites
_discovered_suites = _discover_task_suites()

_SUITES: defaultdict[str, TaskSuite] = defaultdict(
    lambda: None,  # Returns None for missing keys
    _discovered_suites
)

def get_suites() -> dict[str, TaskSuite]:
    return _SUITES

def get_suite(suite_name: str) -> TaskSuite:
    return _SUITES[suite_name]


def get_environment_inspection_function(suite_name):
    """
    Dynamically get the environment inspection function for a given task suite.
    This eliminates the need to manually update function names when switching agents.
    """
    # Get the task suite
    task_suite = get_suite(suite_name)

    # Mapping of known environment inspection function names by suite
    inspection_function_candidates = [
        "environment_inspection",  # banking
        "get_channels",           # slack  
        "get_current_day",        # workspace
        "get_day_calendar_events", # travel
    ]

    # Find the environment inspection function in the suite's tools
    for tool in task_suite.tools:
        if tool.__name__ in inspection_function_candidates:
            return tool

    # Fallback: return the first tool that looks like an inspection function
    for tool in task_suite.tools:
        if any(keyword in tool.__name__.lower() for keyword in ["inspect", "current", "channel", "environment"]):
            return tool

    # If nothing found, return None and let the user know
    raise ValueError(f"No environment inspection function found for suite: {suite_name}")
