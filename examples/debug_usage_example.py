"""
使用增强调试功能的示例

这个脚本展示如何使用新增的debug参数来诊断max turn问题
"""

import sys
import os
from dotenv import load_dotenv

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from agents import Agent
from mav.MAS.framework import MultiAgentSystem
from mav.MAS.terminations import MaxIterationsTermination
from mav.Tasks.load_task_suites import get_suite
from mav.Tasks.utils._transform import convert_to_openai_function_tool

load_dotenv()


async def debug_example():
    """演示如何使用debug功能"""
    
    print("=== 调试Max Turn问题示例 ===\n")
    
    # 1. 设置环境
    banking_task_suite = get_suite("banking")
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
    
    # 2. 创建智能体
    planner_agent = Agent(
        name="Planner Agent",
        instructions="""你是一个银行任务规划代理。
        
对于用户请求，你需要：
1. 分析需求
2. 制定执行计划  
3. 完成规划后输出"规划完成"

保持简洁，对简单任务快速完成规划。""",
        model="gpt-4o-mini",
        tools=[environment_inspection],
    )
    
    banking_agent = Agent(
        name="Banking Agent", 
        instructions="你是银行业务执行代理，负责执行具体操作。",
        model="gpt-4o-mini",
        tools=banking_openai_tools,
    )
    
    # 3. 测试不同配置
    test_cases = [
        {
            "name": "可能有问题的配置",
            "max_iterations": 10,
            "termination_condition": MaxIterationsTermination(1),
            "description": "高max_iterations可能导致不必要的循环"
        },
        {
            "name": "修正后的配置", 
            "max_iterations": 3,
            "termination_condition": MaxIterationsTermination(1),
            "description": "降低max_iterations避免过度循环"
        }
    ]
    
    simple_task = "查询我的账户余额"
    
    for test_case in test_cases:
        print(f"\n{'='*50}")
        print(f"测试: {test_case['name']}")
        print(f"说明: {test_case['description']}")
        print(f"{'='*50}")
        
        # 创建MAS
        mas = MultiAgentSystem(
            agents=[planner_agent, banking_agent],
            runner="planner_executor",
            max_iterations=test_case["max_iterations"],
            termination_condition=test_case["termination_condition"],
            enable_executor_memory=True,
        )
        
        # 创建环境
        env = banking_task_suite.environment_type()
        
        print(f"\n开始执行任务: '{simple_task}'")
        print("启用调试模式...\n")
        
        try:
            # 使用debug=True运行
            result = await mas.query(
                input=simple_task,
                env=env,
                debug=True  # 启用调试输出
            )
            
            print(f"\n✅ 任务完成!")
            print(f"最终输出: {str(result['final_output'])[:200]}...")
            
        except Exception as e:
            print(f"\n❌ 任务执行出错: {e}")
            import traceback
            traceback.print_exc()
        
        input("\n按回车键继续下一个测试...")


if __name__ == "__main__":
    import asyncio
    
    print("Max Turn调试工具使用示例")
    print("这将演示如何使用新增的debug功能来诊断问题\n")
    
    try:
        asyncio.run(debug_example())
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n执行出错: {e}")
    
    print("\n使用方法总结:")
    print("1. 在创建MultiAgentSystem时设置合理的max_iterations")
    print("2. 在调用mas.query()时添加debug=True参数")
    print("3. 观察调试输出，特别关注终止条件检查结果")
    print("4. 根据调试信息调整配置")
