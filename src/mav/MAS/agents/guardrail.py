"""
Guardrail definitions for agents. Simplified version from OpenAI Agents SDK guardrails.
"""
from __future__ import annotations

import inspect

from dataclasses import dataclass
from typing import Callable, Any, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import Agent
from mav.Tasks.base_environment import TaskEnvironment

@dataclass
class GuardrailFunctionOutput:
    """The output of a guardrail function."""

    output_info: Any
    """
    Optional information about the guardrail's output. For example, the guardrail could include
    information about the checks it performed and granular results.
    """

    tripwire_triggered: bool
    """
    Whether the tripwire was triggered. If triggered, the agent's execution will be halted.
    """

@dataclass
class InputGuardrailResult:
    """The result of a guardrail run."""

    guardrail: InputGuardrail
    """
    The guardrail that was run.
    """

    output: GuardrailFunctionOutput
    """The output of the guardrail function."""

@dataclass
class OutputGuardrailResult:
    """The result of a guardrail run."""

    guardrail: OutputGuardrail
    """
    The guardrail that was run.
    """

    agent_output: Any
    """
    The output of the agent that was checked by the guardrail.
    """

    agent: "Agent"
    """
    The agent that was checked by the guardrail.
    """

    output: GuardrailFunctionOutput
    """The output of the guardrail function."""

class GuardrailTripwireTriggered(Exception):
    """Exception raised when a guardrail tripwire is triggered."""
    def __init__(self, guardrail_result):
        self.guardrail_result: OutputGuardrailResult | InputGuardrailResult = guardrail_result
        super().__init__(f"Guardrail '{guardrail_result.guardrail.get_name()}' tripwire triggered")

@dataclass
class InputGuardrail():
    """Input guardrails are checks that run before the agent starts.
    They can be used to do things like:
    - Check if input messages are off-topic
    - Take over control of the agent's execution if an unexpected input is detected

    Guardrails return a `GuardrailResult`. If `result.tripwire_triggered` is `True`,
    the agent's execution will immediately stop, and
    an `InputGuardrailTripwireTriggered` exception will be raised
    """

    guardrail_function: Callable[
        [TaskEnvironment | None, "Agent", str | list[dict[str, Any]] | dict[str, Any]],
        GuardrailFunctionOutput | Awaitable[GuardrailFunctionOutput]
    ]
    """A function that receives the agent input and the context, and returns a
     `GuardrailResult`. The result marks whether the tripwire was triggered, and can optionally
     include information about the guardrail's output.
    """

    name: str | None = None
    """The name of the guardrail, used for tracing. If not provided, we'll use the guardrail
    function's name.
    """

    def get_name(self) -> str:
        if self.name:
            return self.name

        return self.guardrail_function.__name__

    async def run(
        self,
        context: TaskEnvironment | None,
        agent: "Agent",
        input: str | list[dict[str, Any]] | dict[str, Any],
    ) -> InputGuardrailResult:
        if not callable(self.guardrail_function):
            raise TypeError(f"Guardrail function must be callable, got {self.guardrail_function}")

        output = self.guardrail_function(context, agent, input)
        if inspect.isawaitable(output):
            return InputGuardrailResult(
                guardrail=self,
                output=await output,
            )

        return InputGuardrailResult(
            guardrail=self,
            output=output,
        )
    
@dataclass
class OutputGuardrail():
    """Output guardrails are checks that run on the final output of an agent.
    They can be used to do check if the output passes certain validation criteria

    Guardrails return a `GuardrailResult`. If `result.tripwire_triggered` is `True`, an
    `OutputGuardrailTripwireTriggered` exception will be raised.
    """

    guardrail_function: Callable[
        [TaskEnvironment | None, "Agent", Any],
        GuardrailFunctionOutput | Awaitable[GuardrailFunctionOutput]
    ]
    """A function that receives the final agent, its output, and the context, and returns a
     `GuardrailResult`. The result marks whether the tripwire was triggered, and can optionally
     include information about the guardrail's output.
    """

    name: str | None = None
    """The name of the guardrail, used for tracing. If not provided, we'll use the guardrail
    function's name.
    """

    def get_name(self) -> str:
        if self.name:
            return self.name

        return self.guardrail_function.__name__

    async def run(
        self, 
        context: TaskEnvironment | None, 
        agent: "Agent", 
        agent_output: Any
    ) -> OutputGuardrailResult:
        if not callable(self.guardrail_function):
            raise TypeError(f"Guardrail function must be callable, got {self.guardrail_function}")

        output = self.guardrail_function(context, agent, agent_output)
        if inspect.isawaitable(output):
            return OutputGuardrailResult(
                guardrail=self,
                agent=agent,
                agent_output=agent_output,
                output=await output,
            )

        return OutputGuardrailResult(
            guardrail=self,
            agent=agent,
            agent_output=agent_output,
            output=output,
        )