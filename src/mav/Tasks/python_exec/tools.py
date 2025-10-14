"""
Docker-based code execution tools for Python execution tasks.

This module provides tools for executing code in isolated Docker containers.
"""
import docker
import os
import tempfile
from typing import Optional
from mav.Tasks.python_exec.environment import PythonExecEnvironment

# Global Docker client
_docker_client: Optional[docker.DockerClient] = None

def get_docker_client() -> docker.DockerClient:
    """Get or create the Docker client."""
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client

def execute_code_in_docker(
    environment: PythonExecEnvironment,
    code: str,
    language: str = "python"
) -> str:
    """
    Execute code in a Docker container and return the output.
    
    Args:
        environment: The task environment
        code: The code to execute
        language: The programming language (python, bash, etc.)
    
    Returns:
        The output of the code execution
    """
    client = get_docker_client()
    
    # Use the container from environment if available
    container = environment.docker_container
    
    try:
        # Create a temporary file with the code
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{language}', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Copy the file into the container
            with open(temp_file, 'rb') as f:
                container.put_archive('/tmp', f.read())
            
            # Determine the command based on language
            if language == "python":
                exec_cmd = ["python", f"/tmp/{os.path.basename(temp_file)}"]
            elif language == "bash":
                exec_cmd = ["bash", f"/tmp/{os.path.basename(temp_file)}"]
            else:
                exec_cmd = ["/bin/sh", f"/tmp/{os.path.basename(temp_file)}"]
            
            # Execute the code
            exec_result = container.exec_run(exec_cmd)
            
            # Get the output
            output = exec_result.output.decode('utf-8') if exec_result.output else ""
            exit_code = exec_result.exit_code
            
            # Combine output and exit code info
            result = f"Exit Code: {exit_code}\nOutput:\n{output}"
            
            return result
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
    except Exception as e:
        return f"Error executing code: {str(e)}"

def execute_python_code(
    environment: PythonExecEnvironment,
    code: str
) -> str:
    """
    Execute Python code in a Docker container.
    
    Args:
        environment: The task environment
        code: The Python code to execute
    
    Returns:
        The output of the code execution
    """
    return execute_code_in_docker(environment, code, language="python")

def execute_bash_code(
    environment: PythonExecEnvironment,
    code: str
) -> str:
    """
    Execute Bash code in a Docker container.
    
    Args:
        environment: The task environment
        code: The Bash code to execute
    
    Returns:
        The output of the code execution
    """
    return execute_code_in_docker(environment, code, language="bash")

def execute_code(
    environment: PythonExecEnvironment,
    code: str,
    language: str = "python"
) -> str:
    """
    Execute code in a Docker container (generic interface).
    
    Args:
        environment: The task environment
        code: The code to execute
        language: The programming language (python, bash, etc.)
    
    Returns:
        The output of the code execution
    """
    return execute_code_in_docker(environment, code, language)

