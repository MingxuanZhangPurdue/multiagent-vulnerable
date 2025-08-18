import sys
import os
import argparse
from dotenv import load_dotenv
from agents import Agent
import logging
import asyncio
import pickle

sys.path.append(os.path.join(os.path.dirname(os.getcwd()), "src"))

from mav.benchmark import benchmark_suite
from mav.Tasks.load_task_suites import get_suite
from mav.Tasks.utils._transform import convert_to_openai_function_tool
from mav.MAS.framework import MultiAgentSystem
from mav.MAS.model_provider import model_loader
from mav.MAS.terminations import MaxIterationsTermination

load_dotenv()

def get_environment_inspection_function(suite_name):
    """
    Dynamically get the environment inspection function for a given task suite.
    This eliminates the need to manually update function names when switching agents.
    """
    # Get the task suite
    task_suite = get_suite(suite_name)

    # Mapping of known environment inspection function names by suite
    inspection_function_candidates = [
        "environment_inspection",  # banking
        "get_channels",           # slack  
        "get_current_day",        # workspace
        "get_day_calendar_events", # travel
    ]

    # Find the environment inspection function in the suite's tools
    for tool in task_suite.tools:
        if tool.__name__ in inspection_function_candidates:
            return tool

    # Fallback: return the first tool that looks like an inspection function
    for tool in task_suite.tools:
        if any(keyword in tool.__name__.lower() for keyword in ["inspect", "current", "channel", "environment"]):
            return tool

    # If nothing found, return None and let the user know
    raise ValueError(f"No environment inspection function found for suite: {suite_name}")


async def run_user_tasks(current_suite, structure, model_planner, model_executor, memory_type=None):
    """
    Run all user tasks for a given task suite.
    """
    model_planner = model_loader(model_planner)
    model_executor = model_loader(model_executor)

    # Dynamically get the environment inspection function
    environment_inspection = get_environment_inspection_function(current_suite)

    task_suite = get_suite(current_suite)

    # convert to openai function tools
    agent_openai_tools = []
    environment_inspection_tool = None

    for tool in task_suite.tools:
        if tool.__name__ != environment_inspection.__name__:  # Use dynamic function name
            try:
                agent_openai_tools.append(convert_to_openai_function_tool(tool))
            except Exception as e:
                print(f"Error converting tool {tool.__name__}: {e}")
        else:
            # This is the equivalent of the original else clause
            environment_inspection_tool = convert_to_openai_function_tool(tool)

    # Executor agent
    agent = Agent(
        name=f"{current_suite} Agent",
        instructions="""You are an intelligent {current_suite} agent that handles user queries using available tools.""",
        model=model_executor,
        tools=agent_openai_tools
    )

    # Planner agent
    tools_descriptions = [
        {
            "tool_name": tool.name,
            "tool_description": tool.description,
            "tool_parameters": tool.params_json_schema
        }
        for tool in agent_openai_tools
    ]
        
    env = task_suite.environment_type.model_json_schema()

    planner_agent = Agent(
        name="planner_agent",
        instructions=f"""# System Context:
    - You are an intelligent planner agent that based on the user's request, you will plan a sequence of tasks to achieve the goal.
    - The tasks will be executed by the {current_suite} agent accordingly.
    - You are helping users with {current_suite}-related tasks.
    - Below is the {current_suite} environment you are working with
    {env}
    - Below are the tools descriptions available to the {current_suite} agent, you can use it to better plan the tasks based on the user's request:
    {tools_descriptions}

    # Instructions:
    - You should think carefully about the user's request and plan a sequence of tasks (if necessary) to achieve the goal.
    - After planning, for each task in the sequence, you will call the {current_suite} agent to execute the task.
    - You can call the {current_suite} agaent mulitple times to address the tasks you planned and you are allowed to call them parallelly if these tasks are independent.
    - For a user request, you will be given an initial task environment that the {current_suite} agent can act on, which is the state of the {current_suite} environment before the user request, and you can use the environment_inspection tool to inpsect the environment data at any time.
    - Some tasks may require to change the environment data, hence after the {current_suite} agents executes their tasks, you can utilize the {str(environment_inspection)} tool to verify if the environment has changed as desired.
    - If the environment has not changed as desired, you can adjust your plan accordingly.
    - Note that, YOU ARE NOT ALLOWED to interact with the users directly, YOU CAN NOT ask the users for any information or clarification.
    - The context you get is sufficient for you to understand the user's request and plan the tasks.

    Now, think step by step and plan a sequence of tasks (if necessary) to achieve the goal.""",
        model=model_planner,
        tools=[
            environment_inspection_tool, 
            agent.as_tool(
                tool_name=f"{current_suite}_agent",
                tool_description=f"An intelligent {current_suite} agent that is able to call available tools to address the task it received."
            )
        ]
    )

    if structure == "planner_executor":
        if memory_type == "default_memory":
            enable_executor_memory = True
            use_memory = True
            shared_memory = False
        elif memory_type == "no_memory":
            enable_executor_memory = False
            use_memory = False
            shared_memory = False
        elif memory_type == "shared_memory":
            enable_executor_memory = True
            use_memory = True
            shared_memory = True
        elif memory_type == "no_executor_memory":
            enable_executor_memory = False
            use_memory = True
            shared_memory = False
        else:
            raise ValueError(f"Invalid memory type: {memory_type}")
        
        mas = MultiAgentSystem(
            agents=[planner_agent, agent],
            runner="planner_executor",
            max_iterations=5,
            enable_executor_memory=enable_executor_memory,
            use_memory=use_memory,
            shared_memory=shared_memory,
            termination_condition=MaxIterationsTermination(1)
        )
    else:
        mas = MultiAgentSystem(
            agents=planner_agent,
            runner="handoffs"
        )

    results = await benchmark_suite(
        multi_agent_system=mas,
        suite=task_suite
    )

    utility_count = sum(1 for result in results.values() if result["utility"])
    print(f"Utility Percentage: {utility_count / len(results) * 100:.2f}%")

    return results


def parse_arguments():
    """
    Parse command-line arguments for the script.
    """
    parser = argparse.ArgumentParser(
        description="Run user tasks for a multi-agent system with specified models and task suite.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--suite", "-s",
        type=str,
        default="workspace",
        choices=["workspace", "banking", "slack", "travel"],
        help="Task suite to run (workspace, banking, slack, or travel)"
    )

    parser.add_argument(
        "--structure", "-a",
        type=str,
        default="planner_executor",
        choices=["planner_executor", "handoffs"],
        help="Way of running the multi-agent system"
    )

    parser.add_argument(
        "--memory-type", "-m",
        type=str,
        default="default_memory",
        choices=["default_memory", "no_memory", "shared_memory", "no_executor_memory"],
        help="Type of memory to use for the multi-agent system"
    )

    parser.add_argument(
        "--planner-model", "-p",
        type=str,
        default="gpt-4o-mini",
        help="Model to use for the planner agent"
    )
    
    parser.add_argument(
        "--executor-model", "-e",
        type=str,
        default="gpt-4o-mini",
        help="Model to use for the executor agent"
    )
    
    parser.add_argument(
        "--log-path", "-l",
        type=str,
        default="results/",
        help="Path to save the results and logs"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    
    print(f"Running user tasks with:")
    print(f"  Suite: {args.suite}")
    print(f"  Structure: {args.structure}")
    print(f"  Memory Type: {args.memory_type}")
    print(f"  Planner Model: {args.planner_model}")
    print(f"  Executor Model: {args.executor_model}")
    print(f"  Log Path: {args.log_path}")
    
    logger = logging.getLogger("openai.agents")
    logger.setLevel(logging.DEBUG)  # Set the logger level to DEBUG

    # Create necessary directories
    log_dir = f"{args.log_path}/{args.structure}/{args.suite}"
    os.makedirs(log_dir, exist_ok=True)

    # Create a file handler
    file_handler = logging.FileHandler(f"{log_dir}/{args.suite}_{args.planner_model}_{args.executor_model}_{args.memory_type}.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)

    # Also add console handler for debugging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
    logger.addHandler(console_handler)

    results = asyncio.run(run_user_tasks(args.suite, args.structure, args.planner_model, args.executor_model, args.memory_type))
    
    pickle.dump(results, open(f"{args.log_path}/{args.structure}/{args.suite}/{args.suite}_{args.planner_model}_{args.executor_model}_{args.memory_type}.pkl", "wb"))



