from mav.Attacks import BaseAttack, PromptAttack, MemoryAttack, EnvironmentAttack, ToolAttack, InstructionAttack


class PromptAttacks:

    def prompt_attack_0(self, components: AttackComponents):
        prompt = self.attack_config.get("prompt", "")
        # Implement the attack logic here
        pass