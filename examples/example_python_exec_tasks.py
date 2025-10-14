#!/usr/bin/env python3
"""
Example script demonstrating how to access dynamically loaded Python execution attack tasks.

This script shows that tasks loaded from JSON files are registered and accessible in
the same way as manually defined tasks like those in slack/attack_tasks/exhaustion.py

Architecture:
1. python_exec/attack_tasks/__init__.py loads JSON files and creates task classes
2. Task classes are registered with the task_suite (just like @decorator pattern)
3. Tasks are accessible via python_exec_task_suite.user_tasks just like manual tasks
"""
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mav.Tasks.python_exec import python_exec_task_suite

def main():
    print("=" * 80)
    print("Python Execution Attack Tasks - Loaded from JSON")
    print("=" * 80)
    
    # Get all tasks from the suite
    all_tasks = python_exec_task_suite.user_tasks
    
    # Filter for python_exec tasks
    python_exec_tasks = {
        task_id: task 
        for task_id, task in all_tasks.items() 
        if task_id.startswith('python_exec_task_')
    }
    
    print(f"\n✅ Total python_exec tasks loaded: {len(python_exec_tasks)}\n")
    
    # Show first 5 tasks as examples
    print("-" * 80)
    print("Sample Tasks (showing first 5):")
    print("-" * 80)
    
    for i, (task_id, task) in enumerate(list(python_exec_tasks.items())[:5]):
        print(f"\n[Task {i+1}] ID: {task_id}")
        print(f"  Index: {task.INDEX}")
        print(f"  Language: {task.LANGUAGE}")
        print(f"  Expected Result: {task.EXPECTED_RESULT}")
        print(f"  Type: {task.type}")
        print(f"  Goal: {task.GOAL[:80]}...")
        print(f"  Summary: {task.TEXT_SUMMARY[:100]}...")
        
        # Show that we can call methods on the task
        pre_env = python_exec_task_suite.load_default_environment()
        ground_truth_calls = task.ground_truth(pre_env)
        print(f"  Ground Truth Calls: {len(ground_truth_calls)} function call(s)")
        if ground_truth_calls:
            print(f"    - Function: {ground_truth_calls[0].function}")
            print(f"    - Args: {list(ground_truth_calls[0].args.keys())}")
    
    print("\n" + "-" * 80)
    
    # Demonstrate accessing a specific task
    if python_exec_tasks:
        first_task_id = list(python_exec_tasks.keys())[0]
        print(f"\n✅ Accessing specific task by ID: '{first_task_id}'")
        specific_task = python_exec_task_suite.get_user_task_by_id(first_task_id)
        print(f"   Task retrieved: {specific_task.__class__.__name__}")
        print(f"   PROMPT: {specific_task.PROMPT[:150]}...")
    
    print("\n" + "=" * 80)
    print("✅ Tasks can also be imported directly!")
    print("=" * 80)
    # Example of importing a specific task
    # from mav.Tasks.python_exec.attack_tasks import PythonExecAttackTask11
    print("Example: from mav.Tasks.python_exec.attack_tasks import PythonExecAttackTask11")
    
    print("\n" + "=" * 80)
    print("✅ All tasks are accessible just like manually defined tasks!")
    print("=" * 80)

if __name__ == "__main__":
    main()

