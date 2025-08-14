from mav.Attacks.attack import BaseAttack, AttackComponents
class ToolAttack(BaseAttack):
    """A base class for tool-based attacks."""

    def attack(self, components: AttackComponents) -> None:
        """
        config: {
            "method": Literal["description_change"],
            "content": dict[str, dict[str, str]], # agent_name -> (function_name -> new_description)
        } 
        """

        method = self.attack_config.get("method", "description_change")
        content = self.attack_config["content"]

        if method == "description_change":
            self.description_change(components, content)
        else:
            raise ValueError(f"Unknown attack method: {method}")
        
    def description_change(self, components: AttackComponents, content: dict[str, dict[str, str]]) -> None:
        for agent_name, changes in content.items():
            agent = components.agent_dict[agent_name]
            for tool in agent.tools:
                if tool.name in changes:
                    tool.description = changes[tool.name]
