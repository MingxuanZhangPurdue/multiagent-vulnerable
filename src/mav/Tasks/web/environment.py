from pydantic import BaseModel, Field, ConfigDict
from mav.Tasks.base_environment import TaskEnvironment
# from mav.Tasks.web.visualwebarena.browser_env import StateInfo, Trajectory
from typing import Any, Dict  
import numpy as np           
import numpy.typing as npt    

Observation = str | npt.NDArray[np.uint8]
class WebEnvironment(TaskEnvironment):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # state: StateInfo
    # trajectory: Trajectory
    name: str
