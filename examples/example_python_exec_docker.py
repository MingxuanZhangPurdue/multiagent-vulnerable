#!/usr/bin/env python3
"""
Example script demonstrating Docker-based code execution in python_exec tasks.

This script shows how the Docker container is initialized and how tasks can use
the execute_code tools to run code in isolated containers.
"""
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mav.Tasks.python_exec import python_exec_task_suite
from mav.Tasks.python_exec.tools import execute_python_code, execute_bash_code

def main():
    print("=" * 80)
    print("Python Exec Docker Tools Example")
    print("=" * 80)
    
    # Check if Docker container is initialized
    if python_exec_task_suite._docker_container is None:
        print("\n❌ Docker container not initialized!")
        print("   Please ensure Docker is running and accessible.")
        return
    
    print(f"\n✅ Docker container initialized: {python_exec_task_suite._docker_container.name}")
    print(f"   Container ID: {python_exec_task_suite._docker_container.short_id}")
    print(f"   Status: {python_exec_task_suite._docker_container.status}")
    
    # Load default environment
    env = python_exec_task_suite.load_default_environment()
    env.docker_container = python_exec_task_suite._docker_container
    
    print("\n" + "-" * 80)
    print("Testing Python Code Execution")
    print("-" * 80)
    
    # Test 1: Simple Python code
    python_code = """
print("Hello from Docker!")
result = 2 + 2
print(f"2 + 2 = {result}")
"""
    
    print("\n[Test 1] Executing Python code:")
    print("Code:")
    print(python_code)
    
    result = execute_python_code(env, python_code)
    print("\nResult:")
    print(result)
    
    # Test 2: Python code with imports
    python_code2 = """
import math
import sys

print(f"Python version: {sys.version}")
print(f"Pi = {math.pi}")
print(f"Square root of 16 = {math.sqrt(16)}")
"""
    
    print("\n" + "-" * 80)
    print("[Test 2] Executing Python code with imports:")
    print("Code:")
    print(python_code2)
    
    result2 = execute_python_code(env, python_code2)
    print("\nResult:")
    print(result2)
    
    # Test 3: Bash code
    bash_code = """
echo "Hello from Bash in Docker!"
echo "Current directory: $(pwd)"
echo "User: $(whoami)"
ls -la /tmp | head -5
"""
    
    print("\n" + "-" * 80)
    print("[Test 3] Executing Bash code:")
    print("Code:")
    print(bash_code)
    
    result3 = execute_bash_code(env, bash_code)
    print("\nResult:")
    print(result3)
    
    # Test 4: Error handling
    error_code = """
print("This will work")
raise ValueError("This is an intentional error!")
"""
    
    print("\n" + "-" * 80)
    print("[Test 4] Error handling:")
    print("Code:")
    print(error_code)
    
    result4 = execute_python_code(env, error_code)
    print("\nResult:")
    print(result4)
    
    print("\n" + "=" * 80)
    print("✅ Docker-based code execution is working!")
    print("=" * 80)
    
    # Show available tools
    print("\n📋 Available Tools:")
    for tool in python_exec_task_suite.tools:
        print(f"  - {tool.__name__}")

if __name__ == "__main__":
    main()

