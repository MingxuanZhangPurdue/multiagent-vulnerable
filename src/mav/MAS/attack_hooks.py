from mav.Attacks import AttackComponents, BaseAttack

class AttackHooks:

    def __init__(
        self,
        attacks: list[BaseAttack] = []
    ):
        self.attacks = attacks

    """
    Supported events:
    - on_run_start
    """

    async def execute_attacks(self, event_name: str, components: AttackComponents):
        attacks_to_run = [attack for attack in self.attacks if attack.step == event_name]
        for attack in attacks_to_run:
            await attack.attack(components)
