"""
Docker-based code execution tools for Bash execution tasks.

This module provides tools for executing Bash code in isolated Docker containers.
"""
import docker
import os
import tempfile
import tarfile
from typing import Optional
from mav.Tasks.bash_exec.environment import BashExecEnvironment

# Global Docker client
_docker_client: Optional[docker.DockerClient] = None

def get_docker_client() -> docker.DockerClient:
    """Get or create the Docker client."""
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client

def execute_code_in_docker(
    environment: BashExecEnvironment,
    code: str,
    language: str = "bash"
) -> str:
    """
    Execute code in a Docker container and return the output.
    
    Args:
        environment: The task environment
        code: The code to execute
        language: The programming language (bash, sh, etc.)
    
    Returns:
        The output of the code execution
    """
    client = get_docker_client()
    
    # Use the container from environment if available
    container = environment.docker_container
    
    # Check if container is available
    if container is None:
        error_msg = (
            "Error: Docker container is not initialized.\n"
            f"Environment type: {type(environment)}\n"
            f"Environment docker_container: {environment.docker_container}\n"
            "Please ensure Docker is running and the container is created."
        )
        print(error_msg)
        return error_msg
    
    try:
        # Create a temporary file with the code
        suffix = '.sh' if language == 'bash' else f'.{language}'
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Create a tar archive with the code file
            with tempfile.NamedTemporaryFile(suffix='.tar', delete=False) as tar_file:
                with tarfile.open(tar_file.name, 'w') as tar:
                    tar.add(temp_file, arcname=os.path.basename(temp_file))
                
                # Copy the tar archive into the container
                with open(tar_file.name, 'rb') as f:
                    container.put_archive('/tmp', f.read())
                
                # Clean up tar file
                os.remove(tar_file.name)
            
            # Determine the command based on language
            filename = os.path.basename(temp_file)
            if language == "bash":
                exec_cmd = ["bash", f"/tmp/{filename}"]
            else:
                exec_cmd = ["/bin/sh", f"/tmp/{filename}"]
            
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

def execute_bash_code(
    environment: BashExecEnvironment,
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

def execute_sh_code(
    environment: BashExecEnvironment,
    code: str
) -> str:
    """
    Execute shell (sh) code in a Docker container.
    
    Args:
        environment: The task environment
        code: The shell code to execute
    
    Returns:
        The output of the code execution
    """
    return execute_code_in_docker(environment, code, language="sh")

def execute_code(
    environment: BashExecEnvironment,
    code: str,
    language: str = "bash"
) -> str:
    """
    Execute code in a Docker container (generic interface).
    
    Args:
        environment: The task environment
        code: The code to execute
        language: The programming language (bash, sh, etc.)
    
    Returns:
        The output of the code execution
    """
    return execute_code_in_docker(environment, code, language)

