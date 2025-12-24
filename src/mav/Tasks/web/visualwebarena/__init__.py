"""
VisualWebArena browser environment components.
Based on: https://github.com/web-arena-x/visualwebarena

This package provides the core browser automation functionality for web agent tasks.
"""
import os

# Ensure environment variables are set before any imports
if "DATASET" not in os.environ:
    os.environ["DATASET"] = "webarena_prompt_injections"
if "REDDIT" not in os.environ:
    os.environ["REDDIT"] = "http://localhost:9999"
if "GITLAB" not in os.environ:
    os.environ["GITLAB"] = "http://localhost:8023"

# Import browser_env components if available
try:
    from .browser_env import (
        ScriptBrowserEnv,
        Trajectory,
        StateInfo,
    )
    
    # Import action creation functions
    from .browser_env.actions import (
        create_click_action,
        create_type_action,
        create_scroll_action,
        create_goto_url_action,
        create_go_back_action,
        create_go_forward_action,
        create_new_tab_action,
        create_key_press_action,
        create_hover_action,
        create_select_option_action,
        create_stop_action,
    )
    
    BROWSER_ENV_AVAILABLE = True
except ImportError as e:
    BROWSER_ENV_AVAILABLE = False
    _import_error = str(e)
    
    # Create placeholder classes
    class ScriptBrowserEnv:
        def __init__(self, *args, **kwargs):
            raise ImportError(f"browser_env not available: {_import_error}")
    
    Trajectory = None
    StateInfo = None

__all__ = [
    "ScriptBrowserEnv",
    "Trajectory", 
    "StateInfo",
    "BROWSER_ENV_AVAILABLE",
]

# Add action creators to __all__ if available
if BROWSER_ENV_AVAILABLE:
    __all__.extend([
        "create_click_action",
        "create_type_action",
        "create_scroll_action",
        "create_goto_url_action",
        "create_go_back_action",
        "create_go_forward_action",
        "create_new_tab_action",
        "create_key_press_action",
        "create_hover_action",
        "create_select_option_action",
        "create_stop_action",
    ])

