from mav.Attacks.attack import BaseAttack, AttackComponents
class InstructionAttack(BaseAttack):
    """A base class for instruction-based attacks."""

    """
    config: {
        "method": "replace" | "injection",
        "target_agents": List[str],
        "content": Dict[str, str] # agent_name -> instruction content
    }
    """

    async def attack(self, components: AttackComponents) -> None:

        method = self.attack_config["method"]

        if method == "replace":
            target_agents = self.attack_config["target_agents"]
            for agent_name in target_agents:
                components.agent_dict[agent_name].instructions = self.attack_config["content"][agent_name]

        elif method == "injection":
            target_agents = self.attack_config["target_agents"]
            for agent_name in target_agents:
                agent_instructions = components.agent_dict[agent_name].instructions
                components.agent_dict[agent_name].instructions = agent_instructions + self.attack_config["content"][agent_name]