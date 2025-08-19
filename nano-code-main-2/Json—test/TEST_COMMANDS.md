# nanocode1 测试命令和文档

## 🔧 环境准备

```bash
# 确保在项目根目录
cd /Users/gengjiawei/Documents/coding/nano-code-main-2

# 激活环境（如果使用uv）
uv sync

# 安装项目
pip install -e .
```

## 📋 测试命令

### 阶段1：URL分析测试

```bash
# 测试1：分析nano-code仓库
python -m nanocode1 "https://github.com/gusye1234/nano-code"

# 测试2：分析其他仓库
python -m nanocode1 "https://github.com/openai/gpt-4"

# 测试3：分析小型仓库
python -m nanocode1 "https://github.com/requests/requests"
```

### 阶段2：JSON任务执行测试

```bash
# 测试1：使用现有的完整研究计划
python -m nanocode1 test_dissertation_plan.json

# 测试2：使用简化的研究计划
python -m nanocode1 simple_task.json

# 测试3：指定工作目录
python -m nanocode1 test_dissertation_plan.json --working-dir /tmp/test_workspace
```

### 错误处理测试

```bash
# 测试1：无效URL
python -m nanocode1 "invalid-url"

# 测试2：不存在的JSON文件
python -m nanocode1 nonexistent.json

# 测试3：格式错误的JSON
python -m nanocode1 malformed.json
```

## 📝 测试JSON文件

### 1. 简化的研究计划 (simple_task.json)

```json
{
  "dissertation_title": "Simple Code Analysis Task",
  "literature_topic": [
    "Code Quality Analysis",
    "Software Architecture"
  ],
  "experimental_requirements": {
    "code_repository_review": {
      "url": "https://github.com/gusye1234/nano-code",
      "description": "Simple analysis of nano-code repository",
      "analysis_focus": [
        "Code structure",
        "Main components"
      ]
    },
    "reproduction_tasks": [
      {
        "phase": "Quick Analysis",
        "target": "Generate basic project overview",
        "methodology": "Read main files and create summary"
      }
    ],
    "critical_evaluation": {
      "failure_case_study": "Identify any obvious code issues",
      "improvement_directions": [
        "Code organization improvements"
      ]
    }
  },
  "urls": [
    {
      "url": "https://github.com/gusye1234/nano-code",
      "description": "Target repository for analysis"
    }
  ]
}
```

### 2. 多仓库研究计划 (multi_repo_task.json)

```json
{
  "dissertation_title": "Comparative Analysis of AI Coding Agents",
  "literature_topic": [
    "AI Coding Assistants",
    "Code Generation",
    "Agent Architectures"
  ],
  "experimental_requirements": {
    "code_repository_review": {
      "url": "https://github.com/microsoft/vscode-copilot",
      "description": "Analysis of Microsoft Copilot integration",
      "analysis_focus": [
        "Integration patterns",
        "User interface design",
        "Code suggestion mechanisms"
      ]
    },
    "reproduction_tasks": [
      {
        "phase": "Comparative Study",
        "target": "Compare different AI coding approaches",
        "methodology": "Analyze multiple repositories and document differences"
      },
      {
        "phase": "Feature Analysis",
        "target": "Identify key features and capabilities",
        "methodology": "Extract and categorize functionality"
      }
    ],
    "critical_evaluation": {
      "failure_case_study": "Document limitations in current AI coding tools",
      "improvement_directions": [
        "Enhanced context awareness",
        "Better error handling",
        "Improved user experience"
      ]
    }
  },
  "urls": [
    {
      "url": "https://github.com/microsoft/vscode-copilot",
      "description": "Microsoft Copilot VSCode integration"
    },
    {
      "url": "https://github.com/features/copilot",
      "description": "GitHub Copilot documentation"
    }
  ]
}
```

### 3. 错误格式文件 (malformed.json)

```json
{
  "dissertation_title": "Test Error Handling",
  "literature_topic": [
    "Error Testing"
  ],
  "experimental_requirements": {
    "code_repository_review": {
      "url": "https://github.com/test/repo",
      "description": "Test repository",
      // 这里有注释，会导致JSON解析错误
      "analysis_focus": [
        "Test focus"
      ]
    }
    // 缺少逗号，JSON格式错误
    "reproduction_tasks": []
  }
}
```

## 🧪 详细测试步骤

### 测试1：基本URL分析

```bash
# 执行命令
python -m nanocode1 "https://github.com/gusye1234/nano-code"

# 预期行为：
# 1. 显示 "🔍 阶段1：分析代码仓库"
# 2. Agent开始克隆仓库
# 3. 进行代码结构分析
# 4. 生成分析文档
# 5. 显示任务完成摘要
```

### 测试2：JSON任务执行

```bash
# 执行命令
python -m nanocode1 test_dissertation_plan.json

# 预期行为：
# 1. 显示 "🎓 阶段2：执行学术研究计划任务"
# 2. Agent解析研究计划
# 3. 按照计划执行多个研究阶段
# 4. 生成研究报告
# 5. 显示详细的执行摘要
```

### 测试3：错误处理验证

```bash
# 测试无效输入
python -m nanocode1 "not-a-url"

# 预期行为：
# 显示错误信息："❌ 无效输入: not-a-url"
# 提示正确的输入格式
```

## 📊 预期输出示例

### URL分析输出
```
🚀 Agent开始执行任务...
🔍 阶段1：分析代码仓库 https://github.com/gusye1234/nano-code
🔄 执行轮次 1
🔧 调用工具: clone_repo
📝 参数: {"url": "https://github.com/gusye1234/nano-code"}
...
✅ 任务执行完成
📄 代码分析文档已生成

┏━━━━━━━━━━━━━━━━━━━┓
┃ 📊 任务执行摘要    ┃
┡━━━━━━━━━━━━━━━━━━━┩
│ 状态: completed    │
│ 执行阶段: url_analysis │
│ 使用轮次: 5        │
│ 执行步骤: 8 个      │
└───────────────────┘
✅ 任务完成
```

### JSON任务输出
```
🚀 Agent开始执行任务...
🎓 阶段2：执行学术研究计划任务
🔄 执行轮次 1
...
🎯 JSON任务执行完成

┏━━━━━━━━━━━━━━━━━━━┓
┃ 📊 任务执行摘要    ┃
┡━━━━━━━━━━━━━━━━━━━┩
│ 状态: completed    │
│ 执行阶段: json_task_execution │
│ 使用轮次: 12       │
│ 执行步骤: 15 个     │
└───────────────────┘
✅ 任务完成
```

## 🔍 调试技巧

1. **查看详细日志**：Agent会显示每个工具调用的详细信息
2. **检查工作目录**：确保有写入权限
3. **验证网络连接**：URL分析需要网络访问GitHub
4. **JSON格式检查**：使用在线JSON验证器检查格式

现在您可以使用这些命令来测试新实现的两阶段workflow功能！