from prompt_toolkit import prompt
from mav.Attacks.attack import BaseAttack, AttackComponents


class PromptAttack(BaseAttack):

    """Prompt-based attacks"""

    def attack(self, components: AttackComponents) -> None:

        """
        config: {
            "method": Literal["front", "back"], # default is "back"
            "injection": str, # default is ""
        }
        """

        method = self.attack_config.get("method", "back")

        injection = self.attack_config.get("injection", "")

        if method == "back":
            components.input = f"{components.input}\n{injection}"
        elif method == "front":
            components.input = f"{injection}\n{components.input}"
        else:
            raise ValueError(f"Invalid method specified: {method}, should be 'front' or 'back'")