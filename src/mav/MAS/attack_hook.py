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
    # print(f"Executing attacks for event: {event_name}")
    # print(f"Total attack hooks available: {len(attack_hooks)}")
    # print(f"Attack hook steps: {[hook.step for hook in attack_hooks]}")
    
    attack_hooks_to_run = [attack for attack in attack_hooks if attack.step == event_name]
    # print(f"🐛 Attack hooks to run: {attack_hooks_to_run}")
    
    # Store environments for each attack hook
    attack_environments = {}
    
    for attack_hook in attack_hooks_to_run:
        # print(f"Executing attack hook with step: '{attack_hook.step}'")
        
        # Capture pre-attack environment if this is a start event
        pre_env = None
        if event_name.endswith("_start"):
            if hasattr(attack_hook.attack, 'capture_pre_environment'):
                pre_env = attack_hook.attack.capture_pre_environment(components)
        
        # Execute the attack
        attack_hook(iteration, components)
        
        # Capture post-attack environment if this is an end event
        post_env = None
        if event_name.endswith("_end"):
            if hasattr(attack_hook.attack, 'capture_post_environment'):
                post_env = attack_hook.attack.capture_post_environment(components)
        
        # Store environments for this attack hook
        attack_environments[attack_hook] = {
            'pre_environment': pre_env,
            'post_environment': post_env
        }
        
        # If we have both environments, we can evaluate security
        if pre_env is not None and post_env is not None:
            # Extract model_output from components
            model_output = components.final_output
            
            # Call security evaluation with the new signature
            try:
                if hasattr(attack_hook.attack, 'security') and attack_hook.attack.eval_function is not None:
                    # Create args dict similar to what benchmark_suite provides
                    args = {
                        'final_output': model_output,
                        'env': post_env,  # Include post environment in args
                        'iteration': iteration,
                        'event_name': event_name
                    }
                    
                    # Call security with the new 4-parameter signature
                    security_result = attack_hook.attack.security(model_output, pre_env, post_env, args)
                    print(f"🔒 Security evaluation result: {security_result}")
                    
            except Exception as e:
                print(f"❌ Error during security evaluation: {e}")

