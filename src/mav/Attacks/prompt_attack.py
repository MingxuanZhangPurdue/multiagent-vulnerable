from mav.Attacks.attack import BaseAttack


class PromptAttack(BaseAttack):
    """A base class for prompt-based attacks."""

    def __init__(self):
        pass

    def attack(self, prompt: str, injection: str) -> str:
        """
        Perform a prompt attack by injecting a malicious prompt into the prompt.

        Args:
            prompt (str): The original prompt to be attacked.
            injection (str): The malicious prompt to inject.

        Returns:
            str: The modified input with the injected prompt.
        """
        return f"{prompt}\n{injection}"