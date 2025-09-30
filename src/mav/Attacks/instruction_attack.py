import inspect
from typing import Callable, cast
from mav.Attacks.attack import BaseAttack, AttackComponents
class InstructionAttack(BaseAttack):

    """Instructions-based attacks"""
    
    # Class-level tracking to prevent duplicate injections in the same execution
    _injected_agents = set()

    def attack(self, components: AttackComponents) -> None:

        """
        config: {
            "method": Literal["replace", "inject"], # default is "inject"
            "content": dict[str, str] | str # agent_name -> instruction content, default is ""
        }
        """

        method = self.attack_config.get("method", "inject")
        content: dict[str, str] | str = self.attack_config["content"]

        print(f"\n=== INSTRUCTION ATTACK DEBUG ===")
        print(f"Attack method: {method}")
        print(f"Attack content: {content}")
        print(f"Available agents: {list(components.agent_dict.keys())}")
        
        # Print original instructions before attack
        print(f"\n--- BEFORE ATTACK ---")
        for agent_name, agent in components.agent_dict.items():
            print(f"Agent '{agent_name}' original instructions:")
            print(f"  Length: {len(agent.instructions) if agent.instructions else 0}")
            print(f"  Content:\n{agent.instructions}")
            print(f"  {'='*50}")

        if method == "replace":
            self.replace(components, content)
        elif method == "inject":
            self.inject(components, content)
        else:
            raise ValueError(f"Unknown attack method: {method}")

        # Print modified instructions after attack
        print(f"\n--- AFTER ATTACK ---")
        for agent_name, agent in components.agent_dict.items():
            print(f"Agent '{agent_name}' modified instructions:")
            print(f"  Length: {len(agent.instructions) if agent.instructions else 0}")
            print(f"  Content:\n{agent.instructions}")
            print(f"  {'='*50}")
        print(f"=== END INSTRUCTION ATTACK DEBUG ===\n")

    def replace(self, components: AttackComponents, content: dict[str, str] | str) -> None:
        print(f"  [REPLACE] Starting replace attack with content type: {type(content)}")

        if isinstance(content, str):
            print(f"  [REPLACE] Replacing instructions for ALL agents with: {repr(content[:100])}{'...' if len(content) > 100 else ''}")
            for agent_name, agent in components.agent_dict.items():
                print(f"  [REPLACE] Replacing agent '{agent_name}' instructions")
                agent.instructions = content

        elif isinstance(content, dict):
            print(f"  [REPLACE] Replacing instructions for specific agents: {list(content.keys())}")
            for agent_name, new_instructions in content.items():
                if agent_name in components.agent_dict:
                    print(f"  [REPLACE] Replacing agent '{agent_name}' instructions with: {repr(new_instructions[:100])}{'...' if len(new_instructions) > 100 else ''}")
                    components.agent_dict[agent_name].instructions = new_instructions
                else:
                    print(f"  [REPLACE] WARNING: Agent '{agent_name}' not found in agent_dict!")

        else:
            raise ValueError("Invalid content type specified. Supported types are 'str' and 'dict'.")

    def inject(self, components: AttackComponents, content: dict[str, str] | str) -> None:
        print(f"  [INJECT] Starting inject attack with content type: {type(content)}")

        if isinstance(content, str):
            print(f"  [INJECT] Injecting into ALL agents: {repr(content[:100])}{'...' if len(content) > 100 else ''}")
            for agent_name, agent in components.agent_dict.items():
                # Check if already injected to prevent duplicates
                agent_key = f"{agent_name}_{id(agent)}"
                if agent_key in self._injected_agents:
                    print(f"  [INJECT] SKIPPING agent '{agent_name}' - already injected in this execution")
                    continue
                    
                print(f"  [INJECT] Injecting into agent '{agent_name}'")
                instructions = agent.instructions
                agent.instructions = instructions + content
                self._injected_agents.add(agent_key)

        elif isinstance(content, dict):
            print(f"  [INJECT] Injecting into specific agents: {list(content.keys())}")
            for agent_name, new_instructions in content.items():
                if agent_name in components.agent_dict:
                    # Check if already injected to prevent duplicates
                    agent_key = f"{agent_name}_{id(components.agent_dict[agent_name])}"
                    if agent_key in self._injected_agents:
                        print(f"  [INJECT] SKIPPING agent '{agent_name}' - already injected in this execution")
                        continue
                        
                    print(f"  [INJECT] Injecting into agent '{agent_name}': {repr(new_instructions[:100])}{'...' if len(new_instructions) > 100 else ''}")
                    components.agent_dict[agent_name].instructions += new_instructions
                    self._injected_agents.add(agent_key)
                else:
                    print(f"  [INJECT] WARNING: Agent '{agent_name}' not found in agent_dict!")

        else:
            raise ValueError("Invalid content type specified. Supported types are 'str' and 'dict'.")
    
    # Security method inherited from BaseAttack
    # Override if you need custom logic, otherwise BaseAttack.security() will work