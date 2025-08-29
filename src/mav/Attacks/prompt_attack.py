import copy
import logging
from prompt_toolkit import prompt
from mav.Attacks.attack import BaseAttack, AttackComponents

# Setup logging
logger = logging.getLogger(__name__)


class PromptAttack(BaseAttack):

    """Prompt-based attacks"""

    def __init__(self, attack_config: dict = None, eval_function = None, init_env_function = None):
        super().__init__(attack_config, eval_function)
        self.pre_environment = None
        self.post_environment = None
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
        
        # Capture pre-attack environment state (after initialization)
        self.pre_environment = copy.deepcopy(components.env)
        msg = "📸 Captured pre-attack environment state"
        print(msg)
        logger.info(msg)

        method = self.attack_config.get("method", "back")

        injection = self.attack_config.get("injection", "")

        if method == "back":
            components.input = f"{components.input}\n{injection}"
        elif method == "front":
            components.input = f"{injection}\n{components.input}"
        else:
            raise ValueError(f"Invalid method specified: {method}, should be 'front' or 'back'")

    def capture_post_environment(self, components: AttackComponents):
        """Call this after execution to capture post-attack environment state"""
        self.post_environment = copy.deepcopy(components.env)
        msg = "📸 Captured post-attack environment state"
        print(msg)
        logger.info(msg)
        
    def security(self, args) -> bool:
        """Override to pass captured environments to eval_function"""
        if self.eval_function is None:
            raise ValueError("Eval function is not set")
        
        # Extract model_output from args (the result from benchmark_suite)
        model_output = args.get('final_output', '') if args else ''
        
        # Try to extract post-environment from the execution result if not already captured
        if self.post_environment is None:
            # Look for environment in the args/result structure from benchmark_suite
            try:
                if hasattr(args, 'get'):
                    # The args might be the result dict from benchmark_suite
                    env_data = args.get('env')
                    if env_data:
                        self.post_environment = copy.deepcopy(env_data)
                        msg = "📸 Captured post-environment from execution result"
                        print(msg)
                        logger.info(msg)
            except Exception as e:
                logger.debug(f"Could not extract environment from args: {e}")
        
        # Check if we have both environments available
        if self.pre_environment is not None and self.post_environment is not None:
            # Call eval_function with the signature that matches your task security functions:
            # eval_function(model_output, pre_environment, post_environment, result)
            msg = "🔍 Calling eval_function with real environments (4-parameter signature):"
            print(msg)
            logger.info(msg)
            
            logger.info(f"Pre-environment: {str(self.pre_environment)[:100]}...")
            logger.info(f"Post-environment: {str(self.post_environment)[:100]}...")
            logger.info(f"Model output: {str(model_output)[:100]}...")
            
            result = self.eval_function(model_output, self.pre_environment, self.post_environment, args)
            
            msg = f"Security function result: {result}"
            print(f"   {msg}")
            logger.info(msg)
            return result
        else:
            # Fall back to creating mock environments if real ones aren't available
            msg = "🔍 Creating mock environments for eval_function (fallback)"
            print(msg)
            logger.warning(msg)
            
            logger.info(f"Pre-environment available: {self.pre_environment is not None}")
            logger.info(f"Post-environment available: {self.post_environment is not None}")
            
            # Create mock environments and call with 4-parameter signature
            from mav.Tasks.banking.environment import BankingEnvironment, BankAccount, Transaction, Filesystem, UserAccount
            
            # Create properly initialized mock environments
            def create_mock_banking_env():
                mock_bank_account = BankAccount(
                    balance=1000.0,
                    iban='DE89370400440532013000',
                    transactions=[],
                    scheduled_transactions=[]
                )
                mock_filesystem = Filesystem(files={})
                mock_user_account = UserAccount(
                    first_name='Test',
                    last_name='User', 
                    street='Test Street',
                    city='Test City',
                    password='test123'
                )
                return BankingEnvironment(
                    bank_account=mock_bank_account,
                    filesystem=mock_filesystem,
                    user_account=mock_user_account
                )
            
            mock_pre = create_mock_banking_env() if self.pre_environment is None else self.pre_environment
            mock_post = create_mock_banking_env() if self.post_environment is None else self.post_environment
            
            result = self.eval_function(model_output, mock_pre, mock_post, args)
            msg = f"Security function result (mock envs): {result}"
            print(f"   {msg}")
            logger.info(msg)
            return result