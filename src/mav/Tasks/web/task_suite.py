"""
Web task suite for VisualWebArena-style web agent tasks.
Based on the WASP benchmark: https://github.com/facebookresearch/wasp
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

from mav.Tasks.task_suite import TaskSuite
from mav.Tasks.web.environment import WebEnvironment, WebsiteConfig, get_visualwebarena_env_config
from mav.Tasks.web.tools import (
    navigate_to_url, click, type_text, scroll, go_back, go_forward,
    refresh_page, get_page_content, get_current_url, submit_form,
    login, logout, open_new_url, execute_javascript, create_deploy_token,
    create_post, send_message, block_user, get_accessibility_tree,
    take_screenshot,
)

tools = [
    navigate_to_url, click, type_text, scroll, go_back, go_forward,
    refresh_page, get_page_content, get_current_url, submit_form,
    login, logout, open_new_url, execute_javascript, create_deploy_token,
    create_post, send_message, block_user, get_accessibility_tree,
    take_screenshot,
]

web_task_suite = TaskSuite[WebEnvironment](
    tools=tools,
    name="web",
    environment_type=WebEnvironment,
)


def create_browser_env(
    headless: bool = True,
    slow_mo: int = 0,
    observation_type: str = "accessibility_tree",
    viewport_width: int = 1280,
    viewport_height: int = 720,
    config_file: Optional[Path] = None,
):
    try:
        from mav.Tasks.web.visualwebarena.browser_env import ScriptBrowserEnv
        browser_env = ScriptBrowserEnv(
            headless=headless,
            slow_mo=slow_mo,
            observation_type=observation_type,
            viewport_size={"width": viewport_width, "height": viewport_height},
        )
        if config_file:
            browser_env.setup(config_file=config_file)
        else:
            browser_env.setup()
        return browser_env
    except ImportError as e:
        print(f"Warning: Could not import visualwebarena browser_env: {e}")
        return None
    except Exception as e:
        print(f"Warning: Failed to create browser environment: {e}")
        return None


def create_default_environment(
    reddit_domain: Optional[str] = None,
    gitlab_domain: Optional[str] = None,
    attacker_domain: str = "attacker.com",
    with_browser: bool = False,
    headless: bool = True,
) -> WebEnvironment:
    config = get_visualwebarena_env_config()
    reddit_url = reddit_domain or config["reddit"]["url"]
    gitlab_url = gitlab_domain or config["gitlab"]["url"]
    
    env = WebEnvironment(
        name="web",
        attacker_domain=attacker_domain,
        websites={
            "gitlab": WebsiteConfig(
                name="gitlab", domain=gitlab_url,
                credentials={"username": config["gitlab"]["username"], "password": config["gitlab"]["password"]}
            ),
            "reddit": WebsiteConfig(
                name="reddit", domain=reddit_url,
                credentials={"username": config["reddit"]["username"], "password": config["reddit"]["password"]}
            )
        }
    )
    if with_browser:
        browser_env = create_browser_env(headless=headless)
        env.set_browser_env(browser_env)
    return env


original_load_default = web_task_suite.load_default_environment

def load_default_environment_with_websites() -> WebEnvironment:
    try:
        env = original_load_default()
    except Exception:
        env = create_default_environment()
    return env

web_task_suite.load_default_environment = load_default_environment_with_websites


def get_browser_env_from_task_environment(env: WebEnvironment):
    return env.get_browser_env()


def execute_browser_action(env: WebEnvironment, action: Dict[str, Any]) -> Dict[str, Any]:
    browser_env = env.get_browser_env()
    if browser_env is None:
        return {"error": "No browser environment available"}
    try:
        observation, reward, terminated, truncated, info = browser_env.step(action)
        return {"observation": observation, "reward": reward, "terminated": terminated, "truncated": truncated, "info": info}
    except Exception as e:
        return {"error": str(e)}


def close_browser_env(env: WebEnvironment):
    browser_env = env.get_browser_env()
    if browser_env is not None:
        browser_env.close()
        env.set_browser_env(None)
