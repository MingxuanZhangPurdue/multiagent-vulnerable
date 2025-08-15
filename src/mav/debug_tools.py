"""
调试工具集：帮助诊断多智能体系统中的问题
"""
import json
from typing import Any, Dict, List
from mav.MAS.terminations import BaseTermination
from mav.MAS.tracking_framework import TrackedMultiAgentSystem


def analyze_termination_condition(termination_condition: BaseTermination, 
                                 iteration: int = 0, 
                                 mock_results: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """分析终止条件的行为"""
    
    if mock_results is None:
        mock_results = [
            {"role": "assistant", "content": "I need to plan the tasks."},
            {"role": "assistant", "content": "Task completed successfully."}
        ]
    
    analysis = {
        "termination_type": type(termination_condition).__name__,
        "test_results": []
    }
    
    # 测试不同的迭代次数
    for test_iteration in range(5):
        try:
            result = termination_condition(iteration=test_iteration, results=mock_results)
            analysis["test_results"].append({
                "iteration": test_iteration,
                "result": result,
                "should_terminate": result
            })
        except Exception as e:
            analysis["test_results"].append({
                "iteration": test_iteration,
                "result": None,
                "error": str(e)
            })
    
    # 添加特定类型的分析
    if hasattr(termination_condition, 'max_iterations'):
        analysis["max_iterations"] = termination_condition.max_iterations
        analysis["warning"] = f"将在迭代 {termination_condition.max_iterations} 时终止"
    
    if hasattr(termination_condition, 'termination_message'):
        analysis["termination_message"] = termination_condition.termination_message
        analysis["warning"] = f"需要在输出中找到消息: '{termination_condition.termination_message}'"
    
    return analysis


def diagnose_max_turn_issue(mas: TrackedMultiAgentSystem, 
                           expected_simple_task: str = "获取我的账户余额") -> Dict[str, Any]:
    """诊断简单任务为什么会达到最大轮次"""
    
    diagnosis = {
        "system_config": {
            "runner_type": mas.runner,
            "max_iterations": mas.max_iterations,
            "termination_condition": type(mas.termination_condition).__name__ if mas.termination_condition else "None",
            "use_memory": mas.use_memory,
            "shared_memory": mas.shared_memory,
            "enable_executor_memory": mas.enable_executor_memory
        },
        "potential_issues": [],
        "recommendations": []
    }
    
    # 检查常见问题
    if mas.runner == "planner_executor":
        if mas.termination_condition is None:
            diagnosis["potential_issues"].append("没有设置终止条件，只能依赖最大迭代次数")
            diagnosis["recommendations"].append("设置合适的终止条件，如MessageTermination")
        
        if hasattr(mas.termination_condition, 'max_iterations'):
            max_term = mas.termination_condition.max_iterations
            if max_term >= mas.max_iterations:
                diagnosis["potential_issues"].append(
                    f"终止条件的最大迭代次数({max_term})大于等于系统最大迭代次数({mas.max_iterations})"
                )
                diagnosis["recommendations"].append("调整终止条件的max_iterations参数")
        
        if mas.max_iterations > 5:
            diagnosis["potential_issues"].append(f"最大迭代次数设置过高({mas.max_iterations})")
            diagnosis["recommendations"].append("对于简单任务，建议设置max_iterations=3-5")
    
    # 分析终止条件
    if mas.termination_condition:
        term_analysis = analyze_termination_condition(mas.termination_condition)
        diagnosis["termination_analysis"] = term_analysis
        
        # 检查是否第一次迭代就应该终止
        first_iter_result = term_analysis["test_results"][0] if term_analysis["test_results"] else None
        if first_iter_result and first_iter_result.get("result") == True:
            diagnosis["potential_issues"].append("终止条件在第0次迭代就返回True，可能配置错误")
            diagnosis["recommendations"].append("检查终止条件的逻辑是否正确")
    
    return diagnosis


def create_simple_task_test_config():
    """创建一个适合简单任务的测试配置"""
    from mav.MAS.terminations import MaxIterationsTermination, MessageTermination, OrTermination
    
    configs = {
        "conservative": {
            "max_iterations": 3,
            "termination_condition": MaxIterationsTermination(2),
            "description": "保守配置：最多2次planner调用"
        },
        "message_based": {
            "max_iterations": 5,
            "termination_condition": MessageTermination("完成"),
            "description": "基于消息的终止：当输出包含'完成'时终止"
        },
        "flexible": {
            "max_iterations": 5,
            "termination_condition": OrTermination(
                MaxIterationsTermination(3),
                MessageTermination("完成")
            ),
            "description": "灵活配置：3次迭代或找到'完成'消息时终止"
        }
    }
    
    return configs


def print_diagnosis_report(diagnosis: Dict[str, Any]):
    """打印诊断报告"""
    print("\n" + "="*50)
    print("多智能体系统诊断报告")
    print("="*50)
    
    print("\n系统配置:")
    for key, value in diagnosis["system_config"].items():
        print(f"  {key}: {value}")
    
    if diagnosis["potential_issues"]:
        print(f"\n发现的潜在问题 ({len(diagnosis['potential_issues'])}个):")
        for i, issue in enumerate(diagnosis["potential_issues"], 1):
            print(f"  {i}. {issue}")
    
    if diagnosis["recommendations"]:
        print(f"\n建议 ({len(diagnosis['recommendations'])}个):")
        for i, rec in enumerate(diagnosis["recommendations"], 1):
            print(f"  {i}. {rec}")
    
    if "termination_analysis" in diagnosis:
        print("\n终止条件分析:")
        term_analysis = diagnosis["termination_analysis"]
        print(f"  类型: {term_analysis['termination_type']}")
        
        if "max_iterations" in term_analysis:
            print(f"  最大迭代次数: {term_analysis['max_iterations']}")
        
        if "termination_message" in term_analysis:
            print(f"  终止消息: '{term_analysis['termination_message']}'")
        
        print("  测试结果:")
        for result in term_analysis["test_results"]:
            iteration = result["iteration"]
            if "error" in result:
                print(f"    迭代 {iteration}: 错误 - {result['error']}")
            else:
                print(f"    迭代 {iteration}: {'终止' if result['result'] else '继续'}")
    
    print("\n" + "="*50)


# 快速诊断函数
def quick_diagnose(mas: TrackedMultiAgentSystem):
    """快速诊断系统配置"""
    diagnosis = diagnose_max_turn_issue(mas)
    print_diagnosis_report(diagnosis)
    
    print("\n建议的测试配置:")
    configs = create_simple_task_test_config()
    for name, config in configs.items():
        print(f"\n{name.upper()}:")
        print(f"  {config['description']}")
        print(f"  max_iterations: {config['max_iterations']}")
        print(f"  termination_condition: {type(config['termination_condition']).__name__}")
