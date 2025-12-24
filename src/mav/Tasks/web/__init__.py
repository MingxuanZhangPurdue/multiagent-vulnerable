"""
Web task suite for VisualWebArena-style web agent tasks.
Based on the WASP benchmark: https://github.com/facebookresearch/wasp

This module provides:
- WebEnvironment: Environment for web browser simulation
- Tools for web navigation and interaction
- Attack tasks from WASP benchmark (prompt injection attacks)
- Utility tasks (benign user goals)
- Docker management for GitLab and Reddit containers
"""
import os

# Set environment variables before importing visualwebarena components
if "DATASET" not in os.environ:
    os.environ["DATASET"] = "webarena_prompt_injections"
if "REDDIT" not in os.environ:
    os.environ["REDDIT"] = "http://localhost:9999"
if "GITLAB" not in os.environ:
    os.environ["GITLAB"] = "http://localhost:8023"

# Import environment
from mav.Tasks.web.environment import (
    WebEnvironment,
    BrowserState,
    WebsiteConfig,
    ExfilData,
    ActionHistory,
    get_visualwebarena_env_config,
)

# Import task suite
from mav.Tasks.web.task_suite import (
    web_task_suite,
    create_browser_env,
    create_default_environment,
    get_browser_env_from_task_environment,
    execute_browser_action,
    close_browser_env,
)

# Import tools
from mav.Tasks.web.tools import (
    navigate_to_url,
    click,
    type_text,
    scroll,
    go_back,
    go_forward,
    refresh_page,
    get_page_content,
    get_current_url,
    submit_form,
    login,
    logout,
    open_new_url,
    execute_javascript,
    create_deploy_token,
    create_post,
    send_message,
    block_user,
    get_accessibility_tree,
    take_screenshot,
)

# Import attack tasks to register them with the task suite
from mav.Tasks.web import attack_tasks

# Import user tasks (utility tasks from WASP benchmark)
from mav.Tasks.web import user_tasks

# Docker setup and management
from mav.Tasks.web.docker_setup import (
    check_docker_available,
    check_container_running,
    setup_web_environments,
    start_container,
    stop_container,
    reset_container,
    get_service_status,
    print_service_status,
)

# Auto-start Docker containers if enabled via environment variable
if os.environ.get("MAV_WEB_AUTO_START_DOCKER", "false").lower() == "true":
    print("MAV_WEB_AUTO_START_DOCKER is true. Attempting to set up web environments...")
    setup_web_environments()

__all__ = [
    # Environment
    "WebEnvironment",
    "BrowserState", 
    "WebsiteConfig",
    "ExfilData",
    "ActionHistory",
    "get_visualwebarena_env_config",
    # Task suite
    "web_task_suite",
    "create_browser_env",
    "create_default_environment",
    "get_browser_env_from_task_environment",
    "execute_browser_action",
    "close_browser_env",
    # Tools
    "navigate_to_url",
    "click",
    "type_text",
    "scroll",
    "go_back",
    "go_forward",
    "refresh_page",
    "get_page_content",
    "get_current_url",
    "submit_form",
    "login",
    "logout",
    "open_new_url",
    "execute_javascript",
    "create_deploy_token",
    "create_post",
    "send_message",
    "block_user",
    "get_accessibility_tree",
    "take_screenshot",
    # Task modules
    "attack_tasks",
    "user_tasks",
    # Docker management
    "check_docker_available",
    "check_container_running",
    "setup_web_environments",
    "start_container",
    "stop_container",
    "reset_container",
    "get_service_status",
    "print_service_status",
]
