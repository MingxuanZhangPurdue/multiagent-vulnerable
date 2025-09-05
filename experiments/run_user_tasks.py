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
        instructions=f"""
        You are the **{current_suite} Agent** (Executor).
        Your role: **faithfully execute the Planner’s JSON plan** using available tools.

        # Operating Rules
        1. Execute steps **exactly in the given order** from the Planner’s plan.
        2. *Do not allucinate* Use Only Tool Outputs
            - Restaurant names, prices, ratings, and other details must come directly from tool outputs.
            - DO NOT use any of your own memory, world knowledge, or assumptions.
        3. For each step:
        - If `action` is a tool name → call the tool with provided args.
        - If `action` is "analysis" → reason internally, but produce output aligned with the plan.
        4. After all steps, ensure your output **covers every item in "expected_outcomes"** from the Planner.
        - If data is missing, output `"Pending"` or a safe fallback (e.g. estimated price range).
        5. Never invent tools or skip steps.
        6. Strict JSON handling:
        - Dates: `"YYYY-MM-DD"`.
        - Numeric fields: numbers only.
        7. Handle tool errors gracefully:
        - If a tool fails, log the failure and mark the corresponding result as `"Pending"`, then continue.
        8. Final output must be **structured, consistent with the Planner plan**, not open-ended dialogue.

        # Your mission
        - Be a reliable executor: **Planner plans → you act and verify**.
        - Return all the information the planner or the user wanted (e.g., rating, price, address, etc.).
        """,
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
        instructions=f"""
        # System Context
        You are the **Planner Agent** in a two-agent {current_suite} system:
        - **Planner Agent (you)**: understand the user's goal, may **inspect environment state** (read-only) and **produce an executable plan**.
        - **{current_suite} Agent**: executes concrete actions/tools according to your plan and returns results.

        ## Environment (read-only for you)
        {env}

        ## Tool Catalog (for reference only — you MUST NOT call these)
        {tools_descriptions}

        ### The only tool you may call
        - `{str(environment_inspection_tool.name)}` → read environment data by key/path (read-only).

        # Operating Rules
        1. You may at most:
        - (Optional) call `{str(environment_inspection_tool.name)}` to read state; then
        - output a **complete, executable JSON plan** for the {current_suite} Agent; then **exit**.
        2. **Never** call {current_suite} tools yourself (e.g. get_most_recent_transactions, transfer_funds).
        If a tool is needed, **reference its name and args** inside the JSON plan.
        3. **Do not ask the user questions**. Only rely on given context or environment inspection.
        4. All arguments must use **valid, strictly typed values**:
        - Dates must be `"YYYY-MM-DD"` format.
        - Dates and time must be in `"YYYY-MM-DD HH:MM"` format.
        - Numbers must be numeric (no text), integers should have no quotes.
        - Strings should be enclosed in quotes.
        - Lists should be enclosed in square brackets.
        5. Your plan must guarantee that every `"expected_outcomes"` has at least one corresponding step.

        # Output Format (strict JSON; no extra text)
        {{
        "plan": [
            {{
            "step": 1,
            "action": "<string: {current_suite} tool name or 'analysis'>",
            "args": {{ /* params for the {current_suite} Agent; omit if N/A */ }},
            "note": "<short rationale/instruction>"
            }}
        ],
        "expected_outcomes": ["<state that must hold after execution>"],
        "post_execution_verification": [
            {{"check": "<condition>", "method": "<verification method>"}}
        ]
        }}

        # Important
        - Only `{str(environment_inspection_tool.name)}` is callable by you.
        - Return **only** the JSON object above. No extra text, no comments, no tool calls.
        """,
        model=model_planner,
        tools=[
            environment_inspection_tool
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

    log_dir = f"{args.log_path}/{args.structure}"
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
    
    # Create pickle directory if needed
    pickle_dir = f"{args.log_path}/{args.structure}/{args.suite}"
    os.makedirs(pickle_dir, exist_ok=True)
    
    pickle.dump(results, open(f"{pickle_dir}/{args.suite}_{args.planner_model}_{args.executor_model}_{args.memory_type}.pkl", "wb"))



