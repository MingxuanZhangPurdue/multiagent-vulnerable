import docker
from mav.Tasks.task_suite import TaskSuite
from mav.Tasks.python_exec.environment import PythonExecEnvironment
from mav.Tasks.python_exec.tools import (
    execute_python_code,
    execute_bash_code,
)

tools = [
    execute_python_code,
    execute_bash_code,
]

python_exec_task_suite = TaskSuite[PythonExecEnvironment](
    tools=tools,
    name="python_exec",
    environment_type=PythonExecEnvironment,
)

# Initialize Docker container for the task suite
def _init_docker_container():
    """Initialize a Docker container for code execution."""
    try:
        client = docker.from_env()
        
        # Pull the image if not exists (use a lightweight Python image)
        image_name = "python:3.11-slim"
        try:
            client.images.get(image_name)
        except docker.errors.ImageNotFound:
            print(f"Pulling Docker image: {image_name}")
            client.images.pull(image_name)
        
        # Create and start a container
        container = client.containers.create(
            image_name,
            command="tail -f /dev/null",  # Keep container running
            detach=True,
            tty=True,
            name="pear_python_exec_container"
        )
        container.start()
        
        print(f"Docker container '{container.name}' created and started")
        return container
        
    except docker.errors.DockerException as e:
        print(f"Warning: Could not initialize Docker container: {e}")
        print("Code execution features will not be available.")
        return None

# Create the Docker container
_docker_container = _init_docker_container()

# Store container reference in the task suite for later use
python_exec_task_suite._docker_container = _docker_container
