from prompt_toolkit import prompt
from mav.Attacks.attack import BaseAttack, AttackComponents


class PromptAttack(BaseAttack):
    """A base class for prompt-based attacks."""

    """
    config: {
        "method": "front" | "back",
        "injection": str
    }
    """

    async def attack(self, components: AttackComponents) -> None:

        method = self.attack_config.get("method", "back")

        injection = self.attack_config.get("injection", "")

        if method == "back":
            components.input = f"{components.input}\n{injection}"
        elif method == "front":
            components.input = f"{injection}\n{components.input}"
        else:
            raise ValueError(f"Invalid method specified: {method}, should be 'front' or 'back'")