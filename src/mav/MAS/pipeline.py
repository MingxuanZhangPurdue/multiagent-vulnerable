from mav.MAS.framework import MultiAgentSystem
class Pipeline:

    def __init__(
        self,
        mas: MultiAgentSystem,  # supported multi-agent frameworks: OpenAI Agents, Autogent, LangGraph, Camel
    ):
        # multiagent system (MAS): OpenAI Agents, Camel, Autogen, LanGraph
        self.mas = mas

    async def query(
        self,
        input,
        env,
        **kwargs
    ):
        return await self.mas.run(input, env, **kwargs)
