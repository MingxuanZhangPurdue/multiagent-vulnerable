try:
    import agents
    from agents import Runner, ToolCallItem, ToolCallOutputItem, MessageOutputItem, ReasoningItem, HandoffCallItem, HandoffOutputItem
except ImportError:
    agents = None

import json
from agentdojo.functions_runtime import FunctionCall

from collections import OrderedDict
class Pipeline:

    def __init__(
        self,
        mas,
    ):
        # multiagent system (MAS): OpenAI Agents, Camel, Autogen, LanGraph
        self.mas = mas

    async def query(
        self,
        input,
        env,
        **kwargs
    ):

        self.mas.run(input, env, **kwargs)
