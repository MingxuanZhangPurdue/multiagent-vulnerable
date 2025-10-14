import docker
from typing import Optional, ClassVar
from mav.Tasks.base_environment import TaskEnvironment

class PythonExecEnvironment(TaskEnvironment):
    """
    Environment for Python execution tasks with Docker container support.
    
    Each environment has its own Docker container for isolated code execution.
    """
    docker_container: Optional[docker.models.containers.Container] = None
    
    class Config:
        arbitrary_types_allowed = True
        fields = {
            'docker_container': {'exclude': True}  # Exclude from serialization
        }