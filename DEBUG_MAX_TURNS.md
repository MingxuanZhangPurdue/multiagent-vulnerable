# 解决简单任务Max Turn问题的调试指南

## 问题描述

在使用多智能体系统时，一些明显很简单的任务（如查询账户余额）却总是达到最大轮次（max turn），导致效率低下和资源浪费。

## 根本原因分析

经过分析，主要原因包括：

1. **`max_iterations` 设置过高**：即使终止条件正确，系统仍可能循环多次
2. **终止条件配置误解**：`MaxIterationsTermination(1)` 实际上是正确的配置
3. **缺乏调试信息**：难以观察每次迭代的实际行为
4. **Planner输出不满足终止条件**：特别是使用`MessageTermination`时

## 解决方案

### 1. 框架增强

已对 `src/mav/MAS/framework.py` 进行增强，添加了详细的调试功能：

```python
# 使用方法
result = await mas.query(
    input="查询我的账户余额",
    env=env,
    debug=True  # 启用调试输出
)
```

调试输出包括：
- 每次迭代的详细信息
- 终止条件检查结果
- Planner和Executor的输入输出
- 工具调用统计
- 性能指标

### 2. 推荐配置

#### 简单任务配置
```python
mas = MultiAgentSystem(
    agents=[planner_agent, banking_agent],
    runner="planner_executor",
    max_iterations=3,  # 关键：降低最大迭代次数
    termination_condition=MaxIterationsTermination(1),
    enable_executor_memory=True,
)
```

#### 复杂任务配置
```python
from mav.MAS.terminations import MessageTermination, OrTermination

mas = MultiAgentSystem(
    agents=[planner_agent, banking_agent],
    runner="planner_executor", 
    max_iterations=5,
    termination_condition=OrTermination(
        MaxIterationsTermination(2),
        MessageTermination("任务完成")
    ),
    enable_executor_memory=True,
)
```

### 3. 调试工具

创建了多个调试工具帮助诊断问题：

#### 快速诊断脚本
```bash
python examples/simple_debug_guide.py
```

#### 交互式调试
```bash
python examples/debug_usage_example.py
```

#### 高级跟踪（如需要）
```python
from mav.MAS.tracking_framework import create_tracked_mas

mas = create_tracked_mas(
    agents=[planner_agent, banking_agent],
    runner="planner_executor",
    max_iterations=3,
    termination_condition=MaxIterationsTermination(1),
    enable_logging=True
)
```

## 常见配置错误

### ❌ 错误配置
```python
# 问题：max_iterations过高
mas = MultiAgentSystem(
    max_iterations=10,  # 太高了！
    termination_condition=MaxIterationsTermination(1)
)
```

### ✅ 正确配置
```python
# 解决：降低max_iterations
mas = MultiAgentSystem(
    max_iterations=3,   # 合理的上限
    termination_condition=MaxIterationsTermination(1)
)
```

## 调试步骤

1. **启用调试模式**
   ```python
   result = await mas.query(input=task, env=env, debug=True)
   ```

2. **观察关键指标**
   - 每次迭代的终止条件检查结果
   - Planner的实际输出内容
   - 是否在预期的迭代次数内终止

3. **调整配置**
   - 如果总是达到max_iterations：降低该值
   - 如果终止条件从不满足：检查Planner的instructions
   - 如果需要更灵活的终止：使用OrTermination

4. **验证效果**
   - 在简单任务上测试新配置
   - 确认不再出现不必要的max turn

## 性能优化建议

1. **针对简单任务**：
   - `max_iterations = 3`
   - `MaxIterationsTermination(1)`
   - 使用更快的模型（如gpt-4o-mini）

2. **针对复杂任务**：
   - `max_iterations = 5`
   - 组合终止条件
   - 优化Planner的instructions

3. **通用建议**：
   - 定期使用debug模式验证系统行为
   - 为不同类型的任务设置不同的配置
   - 监控token使用量和执行时间

## 文件说明

- `src/mav/MAS/framework.py`：增强的框架（添加debug支持）
- `src/mav/MAS/tracking_framework.py`：高级跟踪功能
- `src/mav/debug_tools.py`：调试工具集
- `examples/debug_usage_example.py`：使用示例
- `examples/simple_debug_guide.py`：诊断指南

## 快速修复

如果你现在就遇到max turn问题，最快的修复方法：

1. 找到你的MultiAgentSystem初始化代码
2. 将`max_iterations`改为3或更小
3. 添加`debug=True`到query调用中观察行为
4. 根据调试输出进一步优化

这应该能立即解决大部分简单任务的max turn问题。
