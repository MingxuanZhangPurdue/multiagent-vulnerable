"""
Docker container management for web environments.
Handles downloading, starting, and managing GitLab and Reddit containers.
"""
import os
import subprocess
import shutil
import time
from typing import Dict, Optional, Tuple

# Docker image and container configurations
WEB_SERVICES = {
    "gitlab": {
        "image": "pjawasp/gitlab-wasp:latest",
        "container_name": "gitlab-wasp",
        "port_mapping": "8023:80",
        "env_var": "GITLAB",
        "default_url": "http://localhost:8023",
        "health_check_path": "/users/sign_in",
        "startup_timeout": 300,  # GitLab takes a while to start
    },
    "reddit": {
        "image": "pjawasp/reddit-wasp:latest", 
        "container_name": "reddit-wasp",
        "port_mapping": "9999:80",
        "env_var": "REDDIT",
        "default_url": "http://localhost:9999",
        "health_check_path": "/",
        "startup_timeout": 60,
    }
}


def check_docker_available() -> bool:
    """Check if Docker is installed and running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_image_exists(image_name: str) -> bool:
    """Check if a Docker image exists locally."""
    try:
        result = subprocess.run(
            ["docker", "images", "-q", image_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_container_running(container_name: str) -> bool:
    """Check if a container is currently running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name={container_name}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_container_exists(container_name: str) -> bool:
    """Check if a container exists (running or stopped)."""
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "-q", "-f", f"name={container_name}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def pull_image(image_name: str) -> bool:
    """Pull a Docker image from registry."""
    print(f"Pulling Docker image: {image_name}...")
    try:
        result = subprocess.run(
            ["docker", "pull", image_name],
            capture_output=False,
            timeout=1800  # 30 minutes timeout for large images
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"Timeout pulling image {image_name}")
        return False
    except FileNotFoundError:
        print("Docker not found")
        return False


def start_container(service_name: str) -> Tuple[bool, str]:
    """
    Start a Docker container for the specified service.
    Returns (success, message).
    """
    if service_name not in WEB_SERVICES:
        return False, f"Unknown service: {service_name}"
    
    config = WEB_SERVICES[service_name]
    container_name = config["container_name"]
    image_name = config["image"]
    port_mapping = config["port_mapping"]
    
    # Check if container is already running
    if check_container_running(container_name):
        return True, f"{service_name} container is already running"
    
    # Check if container exists but is stopped
    if check_container_exists(container_name):
        print(f"Starting existing {service_name} container...")
        try:
            result = subprocess.run(
                ["docker", "start", container_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return True, f"Started existing {service_name} container"
            else:
                # Remove the stopped container and try creating a new one
                subprocess.run(["docker", "rm", container_name], capture_output=True)
        except subprocess.TimeoutExpired:
            return False, f"Timeout starting {service_name} container"
    
    # Check if image exists, pull if not
    if not check_image_exists(image_name):
        print(f"Image {image_name} not found locally, pulling...")
        if not pull_image(image_name):
            return False, f"Failed to pull image {image_name}"
    
    # Run new container
    print(f"Starting new {service_name} container...")
    try:
        host_port, container_port = port_mapping.split(":")
        result = subprocess.run(
            [
                "docker", "run", "-d",
                "--name", container_name,
                "-p", port_mapping,
                "--restart", "unless-stopped",
                image_name
            ],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            # Set environment variable
            os.environ[config["env_var"]] = config["default_url"]
            return True, f"Started {service_name} container on port {host_port}"
        else:
            return False, f"Failed to start {service_name}: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, f"Timeout creating {service_name} container"


def stop_container(service_name: str) -> Tuple[bool, str]:
    """Stop a Docker container for the specified service."""
    if service_name not in WEB_SERVICES:
        return False, f"Unknown service: {service_name}"
    
    config = WEB_SERVICES[service_name]
    container_name = config["container_name"]
    
    if not check_container_running(container_name):
        return True, f"{service_name} container is not running"
    
    try:
        result = subprocess.run(
            ["docker", "stop", container_name],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return True, f"Stopped {service_name} container"
        else:
            return False, f"Failed to stop {service_name}: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, f"Timeout stopping {service_name} container"


def reset_container(service_name: str) -> Tuple[bool, str]:
    """Reset a container to its initial state (stop, remove, start fresh)."""
    if service_name not in WEB_SERVICES:
        return False, f"Unknown service: {service_name}"
    
    config = WEB_SERVICES[service_name]
    container_name = config["container_name"]
    
    # Stop if running
    if check_container_running(container_name):
        stop_result = subprocess.run(
            ["docker", "stop", container_name],
            capture_output=True,
            timeout=60
        )
    
    # Remove if exists
    if check_container_exists(container_name):
        subprocess.run(
            ["docker", "rm", container_name],
            capture_output=True,
            timeout=30
        )
    
    # Start fresh
    return start_container(service_name)


def wait_for_service(service_name: str, timeout: Optional[int] = None) -> bool:
    """Wait for a service to become healthy."""
    if service_name not in WEB_SERVICES:
        return False
    
    config = WEB_SERVICES[service_name]
    url = config["default_url"] + config["health_check_path"]
    timeout = timeout or config["startup_timeout"]
    
    print(f"Waiting for {service_name} to become ready...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            import urllib.request
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status < 500:
                    print(f"{service_name} is ready!")
                    return True
        except Exception:
            pass
        time.sleep(5)
    
    print(f"Timeout waiting for {service_name}")
    return False


def setup_web_environments(services: Optional[list] = None) -> Dict[str, Tuple[bool, str]]:
    """
    Set up all web environments needed for WASP benchmark.
    Returns a dict of service_name -> (success, message).
    """
    if not check_docker_available():
        return {
            "error": (False, "Docker is not available. Please install and start Docker.")
        }
    
    services = services or list(WEB_SERVICES.keys())
    results = {}
    
    for service in services:
        success, message = start_container(service)
        results[service] = (success, message)
        print(f"  {service}: {message}")
        
        if success:
            # Wait a bit for the service to initialize
            wait_for_service(service)
    
    return results


def get_service_status() -> Dict[str, Dict]:
    """Get the current status of all web services."""
    status = {}
    
    for service_name, config in WEB_SERVICES.items():
        container_name = config["container_name"]
        running = check_container_running(container_name)
        exists = check_container_exists(container_name)
        
        status[service_name] = {
            "running": running,
            "exists": exists,
            "container_name": container_name,
            "url": os.environ.get(config["env_var"], config["default_url"]),
            "image": config["image"],
        }
    
    return status


def print_service_status():
    """Print a formatted status report of all services."""
    print("\n=== Web Environment Status ===")
    print(f"Docker available: {check_docker_available()}")
    print()
    
    status = get_service_status()
    for service, info in status.items():
        state = "🟢 Running" if info["running"] else ("🟡 Stopped" if info["exists"] else "⚪ Not created")
        print(f"{service.upper()}:")
        print(f"  Status: {state}")
        print(f"  URL: {info['url']}")
        print(f"  Container: {info['container_name']}")
        print()


if __name__ == "__main__":
    print_service_status()
    
    response = input("\nDo you want to start the web environments? (y/n): ")
    if response.lower() == 'y':
        results = setup_web_environments()
        print("\n=== Setup Complete ===")
        for service, (success, message) in results.items():
            status = "✓" if success else "✗"
            print(f"{status} {service}: {message}")

