# Agent 集成使用指南

## 概述

本文档介绍了如何使用封装在 `final_launch.py` 中的 `Coding_agent` 类。该类集成了完整的 agent 工作流程，包括搜索决策、代码分析和报告生成功能。

## 核心功能

### Coding_agent 类

`Coding_agent` 类实现了完整的 workflow，包括：

1. **第一次分析流程**：直接进入 coding agent 执行
2. **搜索决策流程**：判断是否需要外部资料搜索
3. **Agent 执行流程**：执行代码分析和报告生成
4. **错误处理**：完善的异常处理和日志记录

## 使用方法

### 基本使用

```python
import asyncio
from final_launch import Coding_agent
from nanocode1.models.dissertation_plan import DissertationPlan

# 创建 agent 实例
agent = Coding_agent(working_dir="/path/to/your/project")

# 加载论文计划
plan = DissertationPlan.from_file("path/to/plan.json")

# 生成报告
async def main():
    report = await agent.generate_report(plan)
    print(f"报告生成完成: {report.is_finish}")
    print(f"报告内容: {report.report}")

asyncio.run(main())
```

### 工作流程说明

#### 1. 第一次分析 (is_first_time=True)

当 `dissertation_plan.is_first_time` 为 `True` 时：
- 跳过搜索决策步骤
- 直接进入 coding agent 执行
- 使用 raw analysis prompt 进行代码仓库分析
- 返回完整的分析报告

#### 2. 非第一次分析 (is_first_time=False)

当 `dissertation_plan.is_first_time` 为 `False` 时：
- 首先运行搜索决策模块
- 判断是否需要外部资料搜索
- 如果需要搜索但响应为空，返回搜索请求
- 如果不需要搜索或已有搜索响应，进入 coding agent 执行

### 返回值说明

`generate_report` 方法返回 `ReportModel` 对象，包含：

- `report`: 主报告内容（字符串）
- `artifacts`: 附件列表（图像、表格、代码、文件等）
- `is_finish`: 是否完成标志（布尔值）

### 错误处理

所有异常都会被捕获并转换为包含错误信息的 `ReportModel`：

```python
if not report.is_finish:
    print(f"执行失败: {report.report}")
else:
    print("执行成功")
```

## 配置说明

### 工作目录

- 如果不指定 `working_dir`，使用当前目录
- 确保工作目录存在且有写入权限
- 建议使用绝对路径

### 环境配置

确保以下配置文件存在：
- `~/.nano_code/config.json`：LLM API 配置
- 包含必要的 API 密钥和模型配置

## 示例：完整的使用流程

```python
import asyncio
import json
from pathlib import Path
from final_launch import Coding_agent
from nanocode1.models.dissertation_plan import (
    DissertationPlan,
    CodeRepositoryReview,
    ReproductionTask,
    CriticalEvaluation,
    ExperimentalRequirements,
    UrlInfo
)

async def analyze_repository():
    """分析代码仓库的完整示例"""
    
    # 1. 创建论文计划
    plan = DissertationPlan(
        is_first_time=True,  # 第一次分析
        dissertation_title="深度学习模型优化研究",
        literature_topic=["深度学习", "模型优化"],
        experimental_requirements=ExperimentalRequirements(
            code_repository_review=CodeRepositoryReview(
                url="https://github.com/your/repo",
                description="目标代码仓库",
                analysis_focus=["模型架构", "训练流程", "性能优化"]
            ),
            reproduction_tasks=[
                ReproductionTask(
                    phase="阶段1",
                    target="复现基础模型",
                    methodology="使用原始代码和数据集"
                )
            ],
            critical_evaluation=CriticalEvaluation(
                failure_case_study="分析模型失败案例",
                improvement_directions=["提高准确率", "减少计算开销"]
            )
        ),
        urls=[
            UrlInfo(
                url="https://arxiv.org/abs/example",
                description="相关论文"
            )
        ]
    )
    
    # 2. 创建 agent 并执行分析
    agent = Coding_agent(working_dir="./analysis_workspace")
    
    try:
        report = await agent.generate_report(plan)
        
        if report.is_finish:
            print("✅ 分析完成")
            print(f"报告长度: {len(report.report)} 字符")
            print(f"附件数量: {len(report.artifacts)}")
            
            # 保存报告
            report.save_json("analysis_report.json")
            
        else:
            print("❌ 分析失败")
            print(f"错误信息: {report.report}")
            
    except Exception as e:
        print(f"执行异常: {str(e)}")

if __name__ == "__main__":
    asyncio.run(analyze_repository())
```

## 注意事项

1. **异步执行**：所有方法都是异步的，需要使用 `await` 调用
2. **资源管理**：临时文件会自动清理，无需手动管理
3. **日志记录**：所有操作都有详细的日志记录
4. **错误恢复**：遇到错误时会返回包含错误信息的报告，而不是抛出异常
5. **云端部署**：设计时考虑了 Daytona 云端运行环境的兼容性

## 扩展和自定义

如需扩展功能，可以：

1. 继承 `Coding_agent` 类
2. 重写特定的私有方法（如 `_execute_coding_agent`）
3. 添加自定义的前处理或后处理逻辑
4. 集成额外的工具或模块

这种设计保持了原有架构的灵活性，同时提供了简洁的使用接口。