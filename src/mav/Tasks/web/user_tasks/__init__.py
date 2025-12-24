"""
User tasks (utility tasks) for web task suite based on WASP benchmark.
https://github.com/facebookresearch/wasp

These are benign tasks that represent legitimate user goals.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from mav.Tasks.base_tasks import UserTask

UTILITY_TASKS_FILE = Path(__file__).parent / "wasp_utility_tasks.json"


def load_wasp_utility_tasks() -> List[Dict[str, Any]]:
    """Load WASP utility tasks from JSON file."""
    if UTILITY_TASKS_FILE.exists():
        with open(UTILITY_TASKS_FILE, 'r') as f:
            return json.load(f)
    return []


def format_task_with_domains(task_text: str, sites: List[str]) -> str:
    """Format task text with actual domain URLs."""
    gitlab_domain = os.environ.get("GITLAB", "http://localhost:8023")
    reddit_domain = os.environ.get("REDDIT", "http://localhost:9999")
    task_text = task_text.replace("{gitlab_domain}", gitlab_domain)
    task_text = task_text.replace("{reddit_domain}", reddit_domain)
    return task_text


class WASPUtilityTask(UserTask):
    """
    User task based on WASP benchmark utility tasks.
    These represent benign user goals.
    """
    
    def __init__(
        self,
        task_id: int,
        task_text: str,
        sites: List[str],
        eval_config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            goal=task_text,
        )
        self.task_id = task_id
        self.task_text = task_text
        self.sites = sites
        self.eval_config = eval_config or {}
    
    def get_formatted_task(self) -> str:
        """Return the task with domain URLs filled in."""
        return format_task_with_domains(self.task_text, self.sites)
    
    def get_start_url(self) -> str:
        """Get the starting URL for this task."""
        gitlab_domain = os.environ.get("GITLAB", "http://localhost:8023")
        reddit_domain = os.environ.get("REDDIT", "http://localhost:9999")
        if "gitlab" in self.sites:
            return gitlab_domain
        elif "reddit" in self.sites:
            return reddit_domain
        return gitlab_domain
    
    def evaluate(self, env, agent_answer: str = "") -> Dict[str, Any]:
        """Evaluate if the task was completed successfully."""
        result = {
            "task_id": self.task_id,
            "task": self.task_text,
            "completed": False,
            "agent_answer": agent_answer,
            "reference": self.eval_config.get("reference_answer_raw_annotation", ""),
            "actions_taken": len(env.action_history.actions),
        }
        result["completed"] = len(agent_answer) > 0 and len(env.action_history.actions) > 0
        return result


def create_wasp_utility_tasks() -> List[WASPUtilityTask]:
    """Create WASPUtilityTask instances from the WASP utility tasks JSON file."""
    tasks_data = load_wasp_utility_tasks()
    tasks = []
    for task_data in tasks_data:
        task = WASPUtilityTask(
            task_id=task_data["task_id"],
            task_text=task_data["task"],
            sites=task_data["sites"],
            eval_config=task_data.get("eval"),
        )
        tasks.append(task)
    return tasks


WASP_UTILITY_TASKS = create_wasp_utility_tasks()


def get_utility_task_by_id(task_id: int) -> Optional[WASPUtilityTask]:
    """Get a utility task by its ID."""
    for task in WASP_UTILITY_TASKS:
        if task.task_id == task_id:
            return task
    return None


def get_utility_tasks_by_site(site: str) -> List[WASPUtilityTask]:
    """Get all utility tasks for a specific site (gitlab/reddit)."""
    return [task for task in WASP_UTILITY_TASKS if site in task.sites]


def register_utility_tasks():
    """Register all WASP utility tasks with the web task suite."""
    try:
        from mav.Tasks.web.task_suite import web_task_suite
        for task in WASP_UTILITY_TASKS:
            web_task_suite.register_user_task(task)
    except Exception as e:
        print(f"Warning: Could not register utility tasks: {e}")


register_utility_tasks()

__all__ = [
    "WASPUtilityTask",
    "WASP_UTILITY_TASKS",
    "get_utility_task_by_id",
    "get_utility_tasks_by_site",
    "load_wasp_utility_tasks",
    "create_wasp_utility_tasks",
]

