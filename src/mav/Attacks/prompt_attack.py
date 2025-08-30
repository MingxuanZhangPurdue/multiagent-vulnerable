import logging
from mav.Attacks.attack import BaseAttack, AttackComponents

# Setup logging
logger = logging.getLogger(__name__)


class PromptAttack(BaseAttack):

    """Prompt-based attacks"""

    def __init__(self, attack_config: dict = None, eval_function = None, init_env_function = None):
        super().__init__(attack_config, eval_function)
        self.init_env_function = init_env_function

    def attack(self, components: AttackComponents) -> None:

        """
        config: {
            "method": Literal["front", "back"], # default is "back"
            "injection": str, # default is ""
        }
        """
        
        # Initialize environment if init function is provided
        if self.init_env_function is not None:
            try:
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
            except Exception as e:
                msg = f"❌ Failed to initialize environment: {e}"
                print(msg)
                logger.error(msg)
        else:
            msg = "ℹ️  No environment initialization required"
            print(msg)
            logger.info(msg)
        
        # Note: Environment capture is now handled by execute_attacks function
        # No need to call capture_pre_environment here anymore

        method = self.attack_config.get("method", "back")

        injection = self.attack_config.get("injection", "")

        if method == "back":
            components.input = f"{components.input}\n{injection}"
        elif method == "front":
            components.input = f"{injection}\n{components.input}"
        else:
            raise ValueError(f"Invalid method specified: {method}, should be 'front' or 'back'")

    # capture_post_environment inherited from BaseAttack
        
    # Security method inherited from BaseAttack
    # Override if you need custom logic, otherwise BaseAttack.security() will work