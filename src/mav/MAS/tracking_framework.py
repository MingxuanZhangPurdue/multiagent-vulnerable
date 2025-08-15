import json
import inspect
import time
import logging
from datetime import datetime
from typing import Any, Literal, get_args, Dict, List
from pydantic import BaseModel
from dataclasses import dataclass, field

from agents import (
    Agent,
    Runner, 
    SQLiteSession,
    TResponseInputItem,
    ModelResponse
)

from mav.MAS.terminations import BaseTermination
from mav.items import FunctionCall
from mav.Tasks.base_environment import TaskEnvironment
from mav.MAS.attack_hook import execute_attacks, AttackHook
from mav.Attacks.attack import AttackComponents
from mav.MAS.framework import MultiAgentSystem


@dataclass
class IterationTrace:
    """跟踪单次迭代的详细信息"""
    iteration: int
    timestamp: datetime
    step: str  # "planner_start", "planner_end", "executor_start", "executor_end"
    agent_name: str
    input_content: str
    output_content: str
    termination_checked: bool = False
    termination_result: bool = False
    termination_reason: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    duration_seconds: float = 0.0
    function_calls: List[Dict[str, Any]] = field(default_factory=list)
    error: str = ""


@dataclass
class TaskTrace:
    """跟踪整个任务执行过程"""
    task_id: str
    start_time: datetime
    end_time: datetime = None
    total_duration: float = 0.0
    max_iterations_reached: bool = False
    termination_condition_met: bool = False
    final_termination_reason: str = ""
    iterations: List[IterationTrace] = field(default_factory=list)
    total_planner_calls: int = 0
    total_executor_calls: int = 0
    total_tokens_used: int = 0
    success: bool = False
    error: str = ""


class TrackedMultiAgentSystem(MultiAgentSystem):
    """增强版的多智能体系统，添加详细的跟踪和调试功能"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_trace: TaskTrace = None
        self.enable_logging = True
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger(f"TrackedMAS_{id(self)}")
        logger.setLevel(logging.DEBUG)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def start_task_trace(self, task_id: str = None):
        """开始跟踪一个新任务"""
        self.current_trace = TaskTrace(
            task_id=task_id or f"task_{int(time.time())}",
            start_time=datetime.now()
        )
        if self.enable_logging:
            self.logger.info(f"开始跟踪任务: {self.current_trace.task_id}")
    
    def end_task_trace(self, success: bool = False, error: str = ""):
        """结束任务跟踪"""
        if self.current_trace:
            self.current_trace.end_time = datetime.now()
            self.current_trace.total_duration = (
                self.current_trace.end_time - self.current_trace.start_time
            ).total_seconds()
            self.current_trace.success = success
            self.current_trace.error = error
            
            if self.enable_logging:
                self.logger.info(f"任务 {self.current_trace.task_id} 完成: "
                               f"成功={success}, 耗时={self.current_trace.total_duration:.2f}s, "
                               f"迭代次数={len(self.current_trace.iterations)}")
    
    def get_task_summary(self) -> Dict[str, Any]:
        """获取任务执行摘要"""
        if not self.current_trace:
            return {}
        
        return {
            "task_id": self.current_trace.task_id,
            "duration": self.current_trace.total_duration,
            "iterations": len(self.current_trace.iterations),
            "planner_calls": self.current_trace.total_planner_calls,
            "executor_calls": self.current_trace.total_executor_calls,
            "tokens_used": self.current_trace.total_tokens_used,
            "max_iterations_reached": self.current_trace.max_iterations_reached,
            "termination_condition_met": self.current_trace.termination_condition_met,
            "final_termination_reason": self.current_trace.final_termination_reason,
            "success": self.current_trace.success,
            "error": self.current_trace.error
        }
    
    def print_detailed_trace(self):
        """打印详细的执行轨迹"""
        if not self.current_trace:
            print("没有可用的轨迹数据")
            return
        
        print(f"\n=== 任务执行轨迹: {self.current_trace.task_id} ===")
        print(f"总耗时: {self.current_trace.total_duration:.2f}秒")
        print(f"总迭代数: {len(self.current_trace.iterations)}")
        print(f"Planner调用次数: {self.current_trace.total_planner_calls}")
        print(f"Executor调用次数: {self.current_trace.total_executor_calls}")
        print(f"总Token使用量: {self.current_trace.total_tokens_used}")
        print(f"是否达到最大迭代次数: {self.current_trace.max_iterations_reached}")
        print(f"终止条件是否满足: {self.current_trace.termination_condition_met}")
        print(f"最终终止原因: {self.current_trace.final_termination_reason}")
        print(f"任务成功: {self.current_trace.success}")
        
        print("\n=== 详细迭代轨迹 ===")
        for trace in self.current_trace.iterations:
            print(f"\n--- 迭代 {trace.iteration} - {trace.step} ---")
            print(f"智能体: {trace.agent_name}")
            print(f"时间: {trace.timestamp.strftime('%H:%M:%S.%f')[:-3]}")
            print(f"耗时: {trace.duration_seconds:.2f}秒")
            
            if trace.input_content:
                print(f"输入 (前100字符): {trace.input_content[:100]}...")
            if trace.output_content:
                print(f"输出 (前100字符): {trace.output_content[:100]}...")
            
            if trace.termination_checked:
                print(f"终止条件检查: {trace.termination_result} - {trace.termination_reason}")
            
            if trace.function_calls:
                print(f"函数调用数: {len(trace.function_calls)}")
            
            if trace.usage:
                print(f"Token使用: {trace.usage}")
            
            if trace.error:
                print(f"错误: {trace.error}")
    
    async def run_planner_executor(
        self,
        input: str | list[TResponseInputItem],
        env: TaskEnvironment,
        attack_hooks: list[AttackHook] | None = None,
    ) -> dict[str, Any]:
        """增强版的planner_executor运行方法，添加详细跟踪"""
        
        # 开始任务跟踪
        if not self.current_trace:
            self.start_task_trace()
        
        usage: dict[str, list[dict[str, int]]] = {
            "planner": [],
            "executor": []
        }

        planner = self.agents[0]
        executor = self.agents[1]
        iteration = 0

        planner_memory = SQLiteSession(session_id="planner_memory") if self.use_memory else None
        executor_memory = planner_memory if self.shared_memory else SQLiteSession(session_id="executor_memory") if self.enable_executor_memory else None

        executor_tool_calls: list[dict[str, Any]] = []

        attack_components = AttackComponents(
            input=input,
            final_output=None,
            memory_dict={
                "planner": planner_memory,
                "executor": executor_memory
            },
            agent_dict={
                "planner": planner,
                "executor": executor
            },
            env=env
        )

        if self.enable_logging:
            self.logger.info(f"开始planner_executor运行，最大迭代次数: {self.max_iterations}")
            self.logger.info(f"终止条件: {type(self.termination_condition).__name__}")

        while iteration < self.max_iterations:
            if self.enable_logging:
                self.logger.debug(f"开始迭代 {iteration}")

            # === PLANNER START ===
            planner_start_time = time.time()
            planner_trace = IterationTrace(
                iteration=iteration,
                timestamp=datetime.now(),
                step="planner_start",
                agent_name=planner.name,
                input_content=str(attack_components.input)[:200]
            )

            if attack_hooks is not None:
                execute_attacks(attack_hooks=attack_hooks, event_name="on_planner_start", iteration=iteration, components=attack_components)

            try:
                planner_result = await Runner.run(
                    starting_agent=planner,
                    input=attack_components.input,
                    context=env,
                    session=planner_memory,
                )
                
                planner_trace.output_content = str(planner_result.final_output)[:200] if planner_result.final_output else ""
                planner_trace.duration_seconds = time.time() - planner_start_time
                planner_trace.usage = self.extract_usage(planner_result.raw_responses)
                
                self.current_trace.total_planner_calls += 1
                self.current_trace.total_tokens_used += planner_trace.usage.get("total_tokens", 0)
                
            except Exception as e:
                planner_trace.error = str(e)
                planner_trace.duration_seconds = time.time() - planner_start_time
                if self.enable_logging:
                    self.logger.error(f"Planner执行错误: {e}")

            attack_components.final_output = planner_result.final_output

            if attack_hooks is not None:
                execute_attacks(attack_hooks=attack_hooks, event_name="on_planner_end", iteration=iteration, components=attack_components)

            usage["planner"].append(self.extract_usage(planner_result.raw_responses))

            # === 终止条件检查 ===
            planner_trace.termination_checked = True
            try:
                termination_result = self.termination_condition(iteration=iteration, results=planner_result.to_input_list())
                planner_trace.termination_result = termination_result
                
                if termination_result:
                    planner_trace.termination_reason = f"终止条件满足 (迭代{iteration})"
                    self.current_trace.termination_condition_met = True
                    self.current_trace.final_termination_reason = planner_trace.termination_reason
                    
                    if self.enable_logging:
                        self.logger.info(f"终止条件满足，在迭代 {iteration} 退出")
                    
                    # 添加轨迹并结束
                    self.current_trace.iterations.append(planner_trace)
                    break
                else:
                    planner_trace.termination_reason = "终止条件未满足，继续执行"
                    
            except Exception as e:
                planner_trace.termination_reason = f"终止条件检查错误: {str(e)}"
                planner_trace.error = str(e)
                if self.enable_logging:
                    self.logger.error(f"终止条件检查错误: {e}")

            self.current_trace.iterations.append(planner_trace)

            # === EXECUTOR START ===
            attack_components.input = self.cast_output_to_input(planner_result.final_output)
            
            executor_start_time = time.time()
            executor_trace = IterationTrace(
                iteration=iteration,
                timestamp=datetime.now(),
                step="executor_start",
                agent_name=executor.name,
                input_content=str(attack_components.input)[:200]
            )

            if attack_hooks is not None:
                execute_attacks(attack_hooks=attack_hooks, event_name="on_executor_start", iteration=iteration, components=attack_components)

            try:
                executor_result = await Runner.run(
                    executor,
                    input=attack_components.input,
                    context=env,
                    session=executor_memory,
                )
                
                executor_trace.output_content = str(executor_result.final_output)[:200] if executor_result.final_output else ""
                executor_trace.duration_seconds = time.time() - executor_start_time
                executor_trace.usage = self.extract_usage(executor_result.raw_responses)
                
                self.current_trace.total_executor_calls += 1
                self.current_trace.total_tokens_used += executor_trace.usage.get("total_tokens", 0)
                
                # 收集function calls
                for response in executor_result.raw_responses:
                    for item in response.output:
                        if item.type == "function_call":
                            call_info = {
                                "tool_name": item.name,
                                "tool_arguments": item.arguments
                            }
                            executor_tool_calls.append(call_info)
                            executor_trace.function_calls.append(call_info)
                
            except Exception as e:
                executor_trace.error = str(e)
                executor_trace.duration_seconds = time.time() - executor_start_time
                if self.enable_logging:
                    self.logger.error(f"Executor执行错误: {e}")

            attack_components.final_output = executor_result.final_output

            if attack_hooks is not None:
                execute_attacks(attack_hooks=attack_hooks, event_name="on_executor_end", iteration=iteration, components=attack_components)

            usage["executor"].append(self.extract_usage(executor_result.raw_responses))

            self.current_trace.iterations.append(executor_trace)
            
            attack_components.input = self.cast_output_to_input(executor_result.final_output)
            iteration += 1

        # 检查是否达到最大迭代次数
        if iteration >= self.max_iterations:
            self.current_trace.max_iterations_reached = True
            self.current_trace.final_termination_reason = f"达到最大迭代次数 ({self.max_iterations})"
            if self.enable_logging:
                self.logger.warning(f"达到最大迭代次数 {self.max_iterations}，强制退出")

        # 结束任务跟踪
        self.end_task_trace(success=True)

        return {
            "final_output": planner_result.final_output,
            "usage": usage,
            "function_calls": self.cast_to_function_calls(executor_tool_calls),
            "trace_summary": self.get_task_summary()
        }


def create_tracked_mas(
    agents: Agent | list[Agent],
    runner: Literal["handoffs", "sequential", "planner_executor"],
    termination_condition: list[BaseTermination] | None = None,
    max_iterations: int = 10,
    enable_executor_memory: bool = True,
    shared_memory: bool = False,
    use_memory: bool = True,
    enable_logging: bool = True,
) -> TrackedMultiAgentSystem:
    """创建一个带跟踪功能的多智能体系统"""
    mas = TrackedMultiAgentSystem(
        agents=agents,
        runner=runner,
        termination_condition=termination_condition,
        max_iterations=max_iterations,
        enable_executor_memory=enable_executor_memory,
        shared_memory=shared_memory,
        use_memory=use_memory,
    )
    mas.enable_logging = enable_logging
    return mas
