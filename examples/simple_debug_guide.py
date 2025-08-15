"""
简单的Max Turn调试指南

这个脚本不需要运行，主要提供诊断思路和解决方案
"""

def analyze_max_turn_issue():
    """分析max turn问题的常见原因"""
    
    print("="*60)
    print("多智能体系统 Max Turn 问题诊断指南")
    print("="*60)
    
    print("\n🔍 常见原因分析:")
    
    causes = [
        {
            "问题": "终止条件配置错误",
            "描述": "MaxIterationsTermination(1) 实际上是正确的，表示planner运行1次后检查终止",
            "解决方案": "检查 max_iterations 参数是否过高"
        },
        {
            "问题": "max_iterations 设置过高", 
            "描述": "如果设置为10，即使终止条件是MaxIterationsTermination(1)，也可能循环10次",
            "解决方案": "将 max_iterations 调整为 3-5"
        },
        {
            "问题": "planner输出不满足终止条件",
            "描述": "如果使用MessageTermination，但planner输出中没有包含指定消息",
            "解决方案": "调整planner的instructions或使用更宽松的终止条件"
        },
        {
            "问题": "终止条件逻辑错误",
            "描述": "终止条件的判断逻辑可能有bug",
            "解决方案": "使用简单的MaxIterationsTermination(1-2)进行测试"
        }
    ]
    
    for i, cause in enumerate(causes, 1):
        print(f"\n{i}. {cause['问题']}")
        print(f"   描述: {cause['描述']}")
        print(f"   解决方案: {cause['解决方案']}")
    
    print("\n" + "="*60)
    print("🛠 推荐的调试步骤:")
    print("="*60)
    
    steps = [
        "检查当前的 max_iterations 和 termination_condition 设置",
        "尝试将 max_iterations 降低到 3",
        "使用最简单的 MaxIterationsTermination(1)",
        "在planner的instructions中明确要求输出结束标志",
        "添加日志记录来跟踪每次迭代的状态",
        "检查planner是否真的在第一次就完成了任务规划"
    ]
    
    for i, step in enumerate(steps, 1):
        print(f"{i}. {step}")
    
    print("\n" + "="*60)
    print("📋 推荐配置:")
    print("="*60)
    
    configs = [
        {
            "场景": "简单查询任务",
            "配置": "max_iterations=3, MaxIterationsTermination(1)",
            "说明": "planner规划一次，executor执行，最多3轮"
        },
        {
            "场景": "复杂任务",
            "配置": "max_iterations=5, MaxIterationsTermination(2)",
            "说明": "允许planner重新规划一次"
        },
        {
            "场景": "智能终止",
            "配置": "max_iterations=5, MessageTermination('完成')",
            "说明": "基于planner输出内容判断是否终止"
        }
    ]
    
    for config in configs:
        print(f"\n• {config['场景']}: {config['配置']}")
        print(f"  {config['说明']}")
    
    print("\n" + "="*60)
    print("🔧 快速修复建议:")
    print("="*60)
    
    print("""
如果你的配置是这样的：
```python
mas = MultiAgentSystem(
    agents=[planner_agent, banking_agent],
    runner="planner_executor",
    max_iterations=10,  # 这里可能是问题
    termination_condition=MaxIterationsTermination(1)
)
```

尝试改成：
```python
mas = MultiAgentSystem(
    agents=[planner_agent, banking_agent],
    runner="planner_executor",
    max_iterations=3,   # 降低最大迭代次数
    termination_condition=MaxIterationsTermination(1)
)
```

或者使用更智能的终止条件：
```python
from mav.MAS.terminations import MessageTermination, OrTermination

mas = MultiAgentSystem(
    agents=[planner_agent, banking_agent],
    runner="planner_executor",
    max_iterations=5,
    termination_condition=OrTermination(
        MaxIterationsTermination(2),
        MessageTermination("任务完成")
    )
)
```
""")

    print("\n" + "="*60)
    print("📊 诊断清单:")
    print("="*60)
    
    checklist = [
        "□ max_iterations 是否 > 5？",
        "□ 终止条件是否过于严格？",
        "□ planner的instructions是否清晰？",
        "□ 是否在简单任务上测试过？",
        "□ 是否添加了日志来观察每轮的输出？"
    ]
    
    for item in checklist:
        print(f"  {item}")
    
    print(f"\n如果以上都检查过了还有问题，建议：")
    print(f"1. 在framework.py的run_planner_executor方法中添加print语句")
    print(f"2. 观察每次iteration的termination_condition返回值")
    print(f"3. 检查planner的实际输出内容")


if __name__ == "__main__":
    analyze_max_turn_issue()
