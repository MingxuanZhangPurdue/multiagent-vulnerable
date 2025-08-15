"""
调试最大轮次问题的示例脚本

这个脚本展示了如何：
1. 识别导致max turn的配置问题
2. 使用跟踪功能监控任务执行
3. 分析和优化终止条件
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from agents import Agent
from mav.Tasks.load_task_suites import get_suite
from mav.Tasks.utils._transform import convert_to_openai_function_tool
from mav.MAS.terminations import MaxIterationsTermination, MessageTermination, OrTermination
from mav.MAS.tracking_framework import create_tracked_mas
from mav.debug_tools import quick_diagnose, analyze_termination_condition

load_dotenv()


def setup_agents():
    """设置测试用的智能体"""
    # 加载banking任务套件
    banking_task_suite = get_suite("banking")
    
    # 转换工具
    banking_openai_tools = []
    environment_inspection = None
    
    for tool in banking_task_suite.tools:
        if tool.__name__ != "environment_inspection":
            try:
                banking_openai_tools.append(convert_to_openai_function_tool(tool))
            except Exception as e:
                print(f"Error converting tool {tool.__name__}: {e}")
        else:
            environment_inspection = convert_to_openai_function_tool(tool)
    
    # 创建planner智能体
    planner_agent = Agent(
        name="Planner Agent",
        instructions="""你是一个智能规划代理。对于用户请求，你需要：
1. 分析用户需求
2. 制定执行计划
3. 当计划制定完成后，输出"计划完成"来表示结束

保持简洁，对于简单任务（如查询余额）应该快速完成规划。""",
        model="gpt-4o-mini",  # 使用更快的模型进行测试
        tools=[environment_inspection],
    )
    
    # 创建executor智能体
    banking_agent = Agent(
        name="Banking Agent",
        instructions="""你是一个银行业务智能体，负责执行具体的银行操作。""",
        model="gpt-4o-mini",
        tools=banking_openai_tools,
    )
    
    return planner_agent, banking_agent, banking_task_suite


async def test_different_configurations():
    """测试不同的配置，找出最佳设置"""
    
    print("设置测试环境...")
    planner_agent, banking_agent, banking_task_suite = setup_agents()
    
    # 测试配置
    test_configs = [
        {
            "name": "问题配置 - 容易max turn",
            "max_iterations": 10,
            "termination_condition": MaxIterationsTermination(1),  # 这是常见的错误配置
        },
        {
            "name": "修正配置1 - 降低max_iterations",
            "max_iterations": 3,
            "termination_condition": MaxIterationsTermination(1),
        },
        {
            "name": "修正配置2 - 基于消息终止",
            "max_iterations": 5,
            "termination_condition": MessageTermination("计划完成"),
        },
        {
            "name": "推荐配置 - 混合终止条件",
            "max_iterations": 5,
            "termination_condition": OrTermination(
                MaxIterationsTermination(2),
                MessageTermination("计划完成")
            ),
        }
    ]
    
    simple_task = "查询我的账户余额"
    
    for config in test_configs:
        print(f"\n{'='*60}")
        print(f"测试配置: {config['name']}")
        print(f"{'='*60}")
        
        # 创建跟踪MAS
        mas = create_tracked_mas(
            agents=[planner_agent, banking_agent],
            runner="planner_executor",
            max_iterations=config["max_iterations"],
            termination_condition=config["termination_condition"],
            enable_executor_memory=True,
            enable_logging=True
        )
        
        # 快速诊断配置
        print("\n配置诊断:")
        quick_diagnose(mas)
        
        # 分析终止条件
        print(f"\n终止条件详细分析:")
        term_analysis = analyze_termination_condition(config["termination_condition"])
        print(f"类型: {term_analysis['termination_type']}")
        for result in term_analysis["test_results"][:3]:  # 只显示前3个
            iteration = result["iteration"]
            if "error" in result:
                print(f"  迭代 {iteration}: 错误 - {result['error']}")
            else:
                print(f"  迭代 {iteration}: {'终止' if result['result'] else '继续'}")
        
        # 模拟运行简单任务
        print(f"\n模拟运行任务: '{simple_task}'")
        try:
            # 创建测试环境
            env = banking_task_suite.environment_type()
            
            # 开始跟踪
            mas.start_task_trace(f"test_{config['name'].replace(' ', '_')}")
            
            # 这里我们不实际运行，而是模拟分析
            print("  → 预期行为分析:")
            
            if config["termination_condition"].__class__.__name__ == "MaxIterationsTermination":
                max_iter = config["termination_condition"].max_iterations
                if max_iter == 1:
                    print(f"    ✓ 预期在第1次planner调用后终止")
                else:
                    print(f"    ⚠ 预期在第{max_iter}次planner调用后终止")
            
            if "MessageTermination" in str(type(config["termination_condition"])):
                print("    ✓ 当planner输出包含指定消息时终止")
            
            # 获取摘要
            summary = mas.get_task_summary()
            print(f"  → 配置评分:")
            
            # 简单评分系统
            score = 0
            if config["max_iterations"] <= 5:
                score += 1
                print("    ✓ max_iterations设置合理 (+1)")
            else:
                print("    ✗ max_iterations可能过高 (+0)")
            
            if "MessageTermination" in str(type(config["termination_condition"])):
                score += 2
                print("    ✓ 使用智能终止条件 (+2)")
            elif hasattr(config["termination_condition"], "max_iterations") and config["termination_condition"].max_iterations <= 2:
                score += 1
                print("    ✓ 迭代终止条件合理 (+1)")
            
            print(f"    总分: {score}/3 {'🟢' if score >= 2 else '🟡' if score == 1 else '🔴'}")
            
        except Exception as e:
            print(f"  ✗ 测试配置时出错: {e}")
        
        input("\n按回车键继续下一个配置...")


def main():
    """主函数"""
    print("多智能体系统 Max Turn 调试工具")
    print("=" * 50)
    
    try:
        asyncio.run(test_different_configurations())
    except KeyboardInterrupt:
        print("\n\n用户中断测试")
    except Exception as e:
        print(f"\n\n测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*50)
    print("调试完成！")
    print("\n关键发现:")
    print("1. MaxIterationsTermination(1) 配置通常是正确的")
    print("2. 问题可能在于 max_iterations 设置过高")
    print("3. 使用 MessageTermination 可以更智能地控制终止")
    print("4. OrTermination 可以提供更灵活的终止策略")
    print("\n推荐配置:")
    print("- max_iterations: 3-5")
    print("- termination_condition: MessageTermination('任务完成') 或")
    print("  OrTermination(MaxIterationsTermination(2), MessageTermination('完成'))")


if __name__ == "__main__":
    main()
