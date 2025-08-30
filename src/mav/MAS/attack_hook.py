from typing import Literal
import copy
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
        
        # Always capture pre-attack environment (before attack executes)
        pre_env = copy.deepcopy(components.env)
        
        # Execute the attack
        attack_hook(iteration, components)
        
        # Always capture post-attack environment (after attack executes)
        post_env = copy.deepcopy(components.env)
        
        # Store environments for this attack hook
        attack_environments[attack_hook] = {
            'pre_environment': pre_env,
            'post_environment': post_env
        }
        
        # Store environments on the attack hook object for later access
        # For multi-turn attacks, we need to track first and last execution
        if not hasattr(attack_hook, 'captured_pre_environment') or attack_hook.captured_pre_environment is None:
            attack_hook.captured_pre_environment = pre_env

        
        # Always update post environment to the latest state
        attack_hook.captured_post_environment = post_env
        
        # Track execution count for debugging
        if not hasattr(attack_hook, 'execution_count'):
            attack_hook.execution_count = 0
        attack_hook.execution_count += 1
        

        
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
                    
            except Exception as e:
                print(f"❌ Error during security evaluation: {e}")

