from pydantic import BaseModel

class TaskEnvironment(BaseModel):
    """
    Base class for task environments.
    This class is used to define the environment in which tasks are executed.
    It can be extended to create specific task environments.
    """