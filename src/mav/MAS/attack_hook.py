from typing import Literal
from mav.Attacks import AttackComponents, BaseAttack

class AttackHook:

    def __init__(
        self,
        step: str,
        attack: BaseAttack,
        attack_condition: Literal["max_attacks", "once", "max_iterations", None] = None,
        max_attacks: int = 1,
        max_iterations: int = 1,
        iteration_to_attack: int = 0,
    ):
        self.step = step
        self.attack = attack
        self.attack_counter = 0
        self.attacked = False
        self.attack_condition = attack_condition
        self.max_attacks = max_attacks
        self.max_iterations = max_iterations
        self.iteration_to_attack = iteration_to_attack


    def __call__(self, iteration: int, components: AttackComponents):
        if self.attack_condition is None:
            self.attack.attack(components)
        elif self.attack_condition == "max_attacks":
            if self.attack_counter < self.max_attacks:
                self.attack.attack(components)
        elif self.attack_condition == "once" and iteration == self.iteration_to_attack and not self.attacked:
            self.attack.attack(components)
            self.attacked = True
        elif self.attack_condition == "max_iterations":
            if iteration < self.max_iterations:
                self.attack.attack(components)

        self.attack_counter += 1

def execute_attacks(attack_hooks: list[AttackHook], event_name: str, iteration: int, components: AttackComponents):
    attack_hooks_to_run = [attack for attack in attack_hooks if attack.step == event_name]
    print(f"🐛 Attack hooks to run: {attack_hooks_to_run}")
    for attack_hook in attack_hooks_to_run:
        attack_hook(iteration, components)
        
        # Call capture_post_environment if this is an end event and attack supports it
        # For planner_executor mode, only capture at executor_end (final execution phase)
        # For other modes, capture at any _end event
        has_capture = hasattr(attack_hook.attack, 'capture_post_environment')
        is_end_event = event_name.endswith("_end")
        is_right_event = (event_name == "on_executor_end" or not event_name.startswith("on_planner"))
        
        print(f"🐛 Event: {event_name}, has_capture: {has_capture}, is_end: {is_end_event}, right_event: {is_right_event}")
        
        should_capture = has_capture and is_end_event and is_right_event
        if should_capture:
            print(f"🐛 Calling capture_post_environment for event: {event_name}")
            attack_hook.attack.capture_post_environment(components)

