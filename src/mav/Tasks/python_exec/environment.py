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
    
    def model_copy(self, *, update=None, deep=False):
        """
        Override model_copy to handle Docker container properly.
        Docker container is not copied, only the reference is kept.
        """
        # Temporarily store the docker_container
        docker_container_ref = self.docker_container
        
        # Create a copy without the docker_container
        self.docker_container = None
        try:
            copy = super().model_copy(update=update, deep=deep)
            # Restore the docker_container reference to the copy
            copy.docker_container = docker_container_ref
            return copy
        finally:
            # Restore the original docker_container
            self.docker_container = docker_container_ref