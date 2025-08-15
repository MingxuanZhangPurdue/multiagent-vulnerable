import inspect
from typing import Callable, cast
from mav.Attacks.attack import BaseAttack, AttackComponents
class InstructionAttack(BaseAttack):

    """Instructions-based attacks"""

    def attack(self, components: AttackComponents) -> None:

        """
        config: {
            "method": Literal["replace", "inject"], # default is "inject"
            "content": dict[str, str] | str # agent_name -> instruction content, default is ""
        }
        """

        method = self.attack_config.get("method", "inject")

        content: dict[str, str] | str = self.attack_config["content"]

        if method == "replace":
            self.replace(components, content)
        elif method == "inject":
            self.inject(components, content)
        else:
            raise ValueError(f"Unknown attack method: {method}")

    def replace(self, components: AttackComponents, content: dict[str, str] | str) -> None:

        if isinstance(content, str):
            for agent_name, agent in components.agent_dict.items():
                agent.instructions = content

        elif isinstance(content, dict):
            for agent_name, new_instructions in content.items():
                components.agent_dict[agent_name].instructions = new_instructions

        else:
            raise ValueError("Invalid content type specified. Supported types are 'str' and 'dict'.")

    def inject(self, components: AttackComponents, content: dict[str, str] | str) -> None:

        if isinstance(content, str):
            for agent_name, agent in components.agent_dict.items():
                instructions = agent.instructions
                agent.instructions = instructions + content

        elif isinstance(content, dict):
            for agent_name, new_instructions in content.items():
                components.agent_dict[agent_name].instructions += new_instructions

        else:
            raise ValueError("Invalid content type specified. Supported types are 'str' and 'dict'.")
    