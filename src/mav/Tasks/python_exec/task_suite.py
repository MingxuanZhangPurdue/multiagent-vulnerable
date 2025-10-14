import docker
import subprocess
import os
from pathlib import Path
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
        
        # Use the custom python_exec_environment image
        image_name = "python_exec_environment:latest"
        
        # Check if the image exists, if not, build it automatically
        try:
            client.images.get(image_name)
            print(f"Using existing Docker image: {image_name}")
        except docker.errors.ImageNotFound:
            print(f"Image '{image_name}' not found!")
            print("Building Docker image automatically...")
            
            # Get the path to the build script
            current_dir = Path(__file__).parent
            build_script = current_dir / "environment_utils" / "build_docker_image.sh"
            
            if not build_script.exists():
                print(f"Build script not found at: {build_script}")
                raise FileNotFoundError(f"Build script not found: {build_script}")
            
            # Run the build script
            try:
                result = subprocess.run(
                    ["bash", str(build_script)],
                    cwd=str(build_script.parent),
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(result.stdout)
                print(f"Docker image built successfully!")
            except subprocess.CalledProcessError as e:
                print(f"Failed to build Docker image:")
                print(e.stderr)
                raise
        
        # Check if container already exists and remove it
        try:
            existing_container = client.containers.get("pear_python_exec_container")
            print(f"Removing existing container: {existing_container.name}")
            existing_container.remove(force=True)
        except docker.errors.NotFound:
            pass
        
        # Create and start a container
        container = client.containers.create(
            image_name,
            detach=True,
            tty=True,
            name="pear_python_exec_container"
        )
        container.start()
        
        print(f"Docker container '{container.name}' created and started")
        print(f"Container ID: {container.short_id}")
        print(f"Container status: {container.status}")
        return container
        
    except docker.errors.DockerException as e:
        print(f"Warning: Could not initialize Docker container: {e}")
        print("Code execution features will not be available.")
        return None

# Create the Docker container
_docker_container = _init_docker_container()

# Store container reference in the task suite for later use
python_exec_task_suite._docker_container = _docker_container

# Override load_default_environment to set Docker container
original_load_default = python_exec_task_suite.load_default_environment

def load_default_environment_with_docker():
    """Load default environment and set Docker container."""
    env = original_load_default()
    print(f"Loading default environment, Docker container: {_docker_container}")
    env.docker_container = _docker_container
    print(f"Environment docker_container set to: {env.docker_container}")
    return env

python_exec_task_suite.load_default_environment = load_default_environment_with_docker
