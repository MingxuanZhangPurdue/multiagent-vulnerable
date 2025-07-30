from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

class BaseAttack(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def attack(self):
        pass
