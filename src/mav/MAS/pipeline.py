try:
    import agents
    from agents import Runner, ToolCallItem, ToolCallOutputItem, MessageOutputItem, ReasoningItem, HandoffCallItem, HandoffOutputItem
except ImportError:
    agents = None

from agentdojo.functions_runtime import FunctionCall

from collections import OrderedDict
class Pipeline:

    def __init__(
        self,
        mas,
    ):
        # multiagent system (MAS): OpenAI Agents, Camel, Autogen, LanGraph
        self.mas = mas

    def cast_to_function_call(
        self,
        tool_calls: list[dict],
    ) -> list[FunctionCall]:
        '''
        Converts a list of tool calls to a list of Agentdojo FunctionCall objects.
        '''
        return [
            FunctionCall(
                function=tool_call["tool_name"],
                args = tool_call["tool_arguments"],
            )
            for tool_call in tool_calls
        ]

    async def query(
        self,
        input,
        runtime,
        env,
        messages,
        extra_args,
    ):
        pass

    async def query_openai_agents(
        self,
        input: str,
    ):
        '''
        This method takes an OpenAI Agent as the MAS and an input string.

        When you use the run method in Runner, you pass in a starting agent and input. 
        The input can either be a string (which is considered a user message), or a list of input items, which are the items in the OpenAI Responses API.
        The runner then runs a loop:
        1. We call the LLM for the current agent, with the current input.
        2. The LLM produces its output.
            a. If the LLM returns a final_output, the loop ends and we return the result.
            b. If the LLM does a handoff, we update the current agent and input, and re-run the loop.
            c. If the LLM produces tool calls, we run those tool calls, append the results, and re-run the loop.
        3. If we exceed the max_turns passed, we raise a MaxTurnsExceeded exception.
        '''

        if agents is None:
            raise ImportError("""An OpenAI Agent is passed as the MAS, but the Runner module is not available. 
            Please ensure it is installed and accessible. You can install it using pip:
            pip install openai-agents""")

        try:
            result = await Runner.run(self.mas, input)

            tool_calls = OrderedDict()

            final_output = result.final_output

            for item in result.new_items:
                if isinstance(item, ToolCallItem):
                    tool_calls[item.raw_item.call_id] = {
                        "agent": item.agent.name,
                        "tool_call_id": item.raw_item.call_id,
                        "tool_name": item.raw_item.name,
                        "tool_arguments": item.raw_item.arguments,
                        "tool_output": None, # Initialize tool_output to None
                        "status": item.raw_item.status,
                    }
                elif isinstance(item, ToolCallOutputItem):
                    call_id = item.raw_item.get("call_id")
                    if call_id in tool_calls:
                        tool_calls[call_id]["tool_output"] = item.raw_item.get("output", None)
                elif isinstance(item, HandoffCallItem):
                    tool_calls[item.raw_item.call_id] = {
                        "agent": item.agent.name,
                        "tool_call_id": item.raw_item.call_id,
                        "tool_name": item.raw_item.name,
                        "tool_arguments": item.raw_item.arguments,
                        "tool_output": None, # Initialize tool_output to None
                        "status": item.raw_item.status,
                    }
                elif isinstance(item, HandoffOutputItem):
                    call_id = item.raw_item.get("call_id")
                    if call_id in tool_calls:
                        tool_calls[call_id]["tool_output"] = item.raw_item.get("output", None)

            return {
                "final_output": final_output,
                "tool_calls": list(tool_calls.values()),
            }

        except Exception as e:
            raise RuntimeError(f"An error occurred while running the OpenAI agents: {e}")

    def query_camel_agents(
        self,
        input: str,
    ):
        raise NotImplementedError("Camel agents are not yet implemented in the pipeline.")

    def query_autogen_agents(
        self,
        input: str,
    ):
        raise NotImplementedError("Autogen agents are not yet implemented in the pipeline.")
    
    def query_metagpt_agents(
        self,
        input: str,
    ):
        raise NotImplementedError("LangGraph agents are not yet implemented in the pipeline.")

    def query_langraph_agents(
        self,
        input: str,
    ):
        raise NotImplementedError("LangGraph agents are not yet implemented in the pipeline.")