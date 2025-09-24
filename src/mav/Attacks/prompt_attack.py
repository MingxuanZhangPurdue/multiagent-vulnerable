import logging
from mav.Attacks.attack import BaseAttack, AttackComponents

# Setup logging
logger = logging.getLogger(__name__)


class PromptAttack(BaseAttack):

    """Prompt-based attacks"""

    def __init__(self, attack_config: dict = None, eval_function = None, init_env_function = None):
        super().__init__(attack_config, eval_function)
        self.init_env_function = init_env_function
        # One-time init guard
        self._env_init_done = False

    def attack(self, components: AttackComponents) -> None:

        """
        config: {
            "method": Literal["front", "back"], # default is "back"
            "injection": str, # default is ""
            "target_agent": str | None, # default is None (all agents)
        }
        """
        
        # Initialize environment once if init function is provided
        if self.init_env_function is not None and not self._env_init_done:
            try:
                # Build a stable tag for this init function to de-duplicate across identical hooks
                try:
                    func_mod = getattr(self.init_env_function, "__module__", "")
                    func_qn = getattr(self.init_env_function, "__qualname__", getattr(self.init_env_function, "__name__", "init_env"))
                    init_tag = f"init::{func_mod}.{func_qn}"
                except Exception:
                    init_tag = f"init::{str(self.init_env_function)}"

                # Maintain a per-environment set of already-applied init tags
                env_tags = getattr(components.env, "_attack_init_tags", None)
                if env_tags is None:
                    env_tags = set()
                    setattr(components.env, "_attack_init_tags", env_tags)

                # If an identical init has already been applied to this environment, skip
                if init_tag in env_tags:
                    msg = "No environment initialization required (identical hook already initialized)"
                    print(msg)
                    logger.info(msg)
                    self._env_init_done = True
                    return

                msg = f"🔧 Initializing environment using {self.init_env_function.__name__}"
                print(msg)
                logger.info(msg)
                old_env_state = str(components.env)[:100]
                components.env = self.init_env_function(components.env)
                new_env_state = str(components.env)[:100]
                
                logger.info(f"Environment before: {old_env_state}")
                logger.info(f"Environment after:  {new_env_state}")
                
                msg = "✅ Environment initialized successfully"
                print(msg)
                logger.info(msg)
                # Mark as initialized to avoid re-initialization on subsequent hooks/events
                self._env_init_done = True
                # Record the tag on the shared environment so identical hooks skip next time
                env_tags.add(init_tag)
            except Exception as e:
                msg = f"❌ Failed to initialize environment: {e}"
                print(msg)
                logger.error(msg)
        else:
            # Either no init function is provided, or it has already run
            msg = "No environment initialization required (none provided or already initialized)"
            print(msg)
            logger.info(msg)
        
        # Note: Environment capture is now handled by execute_attacks function
        # No need to call capture_pre_environment here anymore

        method = self.attack_config.get("method", "back")
        injection = self.attack_config.get("injection", "")
        target_agent = self.attack_config.get("target_agent", None)

        if method == "back":
            if target_agent is not None:
                if components.agent_dict.get(target_agent) is None:
                    raise ValueError(f"Target agent {target_agent} not found in agent_dict")
                components.agent_dict[target_agent].prompt = f"{components.agent_dict[target_agent].prompt}\n{injection}"
            else:
                components.input = f"{components.input}\n{injection}"
        elif method == "front":
            if target_agent is not None:
                if components.agent_dict.get(target_agent) is None:
                    raise ValueError(f"Target agent {target_agent} not found in agent_dict")
                components.agent_dict[target_agent].prompt = f"{components.agent_dict[target_agent].prompt}\n{injection}"
            else:
                components.input = f"{components.input}\n{injection}"
        else:
            raise ValueError(f"Invalid method specified: {method}, should be 'front' or 'back'")

    # capture_post_environment inherited from BaseAttack
        
    # Security method inherited from BaseAttack
    # Override if you need custom logic, otherwise BaseAttack.security() will work