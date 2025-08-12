# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在 nanocode1 项目中工作时提供指导。

## Code Architecture

- 编写代码的硬性指标，包括以下原则：
  (1) 对于 Python、JavaScript、TypeScript 等动态语言，尽可能确保每个代码文件不要超过 400 行
  (2) 对于 Java、Go、Rust 等静态语言，尽可能确保每个代码文件不要超过 250 行
  (3) 每层文件夹中的文件，尽可能不超过 8 个。如有超过，需要规划为多层子文件夹

- 除了硬性指标以外，还需要时刻关注优雅的架构设计，避免出现以下可能侵蚀我们代码质量的「坏味道」：
  (1) 僵化 (Rigidity)：系统难以变更，任何微小的改动都会引发一连串的连锁修改。
  (2) 冗余 (Redundancy)：同样的代码逻辑在多处重复出现，导致维护困难且容易产生不一致。
  (3) 循环依赖 (Circular Dependency)：两个或多个模块互相纠缠，形成无法解耦的"死结"，导致难以测试与复用。
  (4) 脆弱性 (Fragility)：对代码一处的修改，导致了系统中其他看似无关部分功能的意外损坏。
  (5) 晦涩性 (Obscurity)：代码意图不明，结构混乱，导致阅读者难以理解其功能和设计。
  (6) 数据泥团 (Data Clump)：多个数据项总是一起出现在不同方法的参数中，暗示着它们应该被组合成一个独立的对象。
  (7) 不必要的复杂性 (Needless Complexity)：用"杀牛刀"去解决"杀鸡"的问题，过度设计使系统变得臃肿且难以理解。

- 【非常重要！！】无论是你自己编写代码，还是阅读或审核他人代码时，都要严格遵守上述硬性指标，以及时刻关注优雅的架构设计。

- 【非常重要！！】无论何时，一旦你识别出那些可能侵蚀我们代码质量的「坏味道」，都应当立即询问用户是否需要优化，并给出合理的优化建议。

- 【非常重要！！】在编写，修改，做出计划时，永远要具有agentic思维。 

## 项目概述

**nanocode1** 是一个受 Gemini Code 启发的自主AI编程助手的 Python 实现。它提供批处理模式的任务自动化功能，具备高级文件操作、Git 仓库分析和 AI 驱动的代码生成能力。

## 开发命令

### 环境管理
- `python -m venv venv` - 创建虚拟环境
- `source venv/bin/activate` (Linux/Mac) 或 `venv\Scripts\activate` (Windows) - 激活虚拟环境
- `deactivate` - 停用虚拟环境
- `pip install -e .` - 以开发模式安装项目
- `pip install -r requirements-dev.txt` - 安装开发依赖（如果可用）

### 核心应用命令 (智能模式)
- `nanocode1 --user-input "分析这些文件的代码质量 main.py config.py"` - Agent自动识别文件并分析
- `nanocode1 --user-input "分析https://github.com/user/repo的代码架构"` - Agent自动克隆Git仓库并分析
- `nanocode1 --user-input "比较本地代码和远程仓库的差异"` - Agent智能识别任务类型
- `nanocode1 --user-input "任务描述" --working-dir /path/to/project` - 设置工作目录

### 🆕 Daytona 代理命令 (智能模式)
- `python3 daytona_proxy.py "分析CSV数据文件 data.csv"` - Agent自动识别文件并上传分析
- `python3 daytona_proxy.py "分析https://github.com/user/project的代码架构"` - Agent自动克隆Git仓库并分析
- `python3 daytona_proxy.py "比较本地main.py和远程仓库的实现差异"` - Agent智能执行复合任务
- `python3 daytona_proxy.py "生成项目技术文档并导出"` - Agent自动选择工具并生成输出

### 测试命令
- `pytest` - 运行所有测试
- `pytest tests/` - 运行 tests 目录中的测试
- `pytest -v` - 以详细输出运行测试
- `pytest --cov=nanocode1` - 运行测试并生成覆盖率报告
- `pytest tests/test_tools.py` - 运行特定测试文件
- `python -m pytest` - 替代的 pytest 执行方式

### 代码质量命令
- `python -m black nanocode1/` - 使用 Black 格式化代码
- `python -m isort nanocode1/` - 排序导入语句
- `python -m flake8 nanocode1/` - 运行代码检查
- `python -m mypy nanocode1/` - 类型检查（如果已配置）

### 包管理
- `pip install -e .` - 以开发模式安装
- `pip list --outdated` - 检查过时的包
- `pip freeze > requirements.txt` - 生成依赖文件

## 技术栈

### 核心技术
- **Python 3.11+** - 主要编程语言
- **OpenAI API** - AI 助手功能的 LLM 集成
- **Rich** - 终端界面和格式化
- **asyncio** - 工具执行的异步编程
- **tiktoken** - OpenAI 模型的令牌计数

### 开发工具
- **pytest** - 支持异步的测试框架
- **pytest-cov** - 覆盖率报告
- **pytest-asyncio** - 异步测试支持
- **gitignore-parser** - Git 忽略文件解析

### AI 和自动化
- **OpenAI GPT 模型** - 核心 AI 推理和代码生成
- **基于工具的架构** - 文件操作的模块化工具系统
- **内存管理** - 基于会话的上下文保持
- **自主执行** - 多轮迭代任务完成

## 项目架构

### 核心结构
```
nanocode1/
├── __init__.py
├── __main__.py              # CLI entry point
├── agent/
│   └── non_interactive_agent.py  # Main autonomous agent
├── agent_tool/
│   ├── tools.py            # Tool registry and imports
│   ├── registry.py         # Tool registration system
│   ├── base.py             # Base tool classes
│   ├── os_tool/            # File system operations
│   ├── Pyhton_Tool/        # Python-specific tools
│   ├── util_tool/          # Utility functions
│   └── git_tool/           # Git repository tools (commented)
├── core/
│   ├── session.py          # Session management
│   └── cost.py             # Cost tracking
├── llm/
│   ├── clients.py          # LLM client implementations
│   └── openai_model.py     # OpenAI model interface
└── utils/
    ├── logger.py           # Logging utilities
    ├── file.py             # File utilities
    ├── paths.py            # Path utilities
    └── tokens.py           # Token management

daytona_management/         # 🆕 Modular Daytona Proxy System
├── __init__.py            # Module exports and documentation
├── config.py              # Configuration management with security (75 lines)
├── sandbox_manager.py     # Daytona sandbox lifecycle management (146 lines)
├── workspace_manager.py   # Workspace setup and file operations (67 lines)
├── file_transfer.py       # File upload/download operations (167 lines)
├── task_executor.py       # nano-code task execution logic (86 lines)
├── proxy.py              # Main coordinator class (123 lines)
└── cli.py                # Command line interface (139 lines)
```

### 🆕 Daytona 集成架构
**daytona_management** 模块提供了完全模块化的 Daytona 沙盒管理系统，解决了原始 595 行单体文件的所有代码质量问题：

#### 模块化设计原则
- ✅ **单一职责原则**: 每个模块专注一个特定功能领域
- ✅ **代码行数限制**: 所有模块都在 400 行以内（符合 CLAUDE.md 要求）
- ✅ **安全增强**: 移除硬编码 API 密钥，使用环境变量
- ✅ **消除代码重复**: 提取共享功能，避免冗余
- ✅ **清晰的模块边界**: 明确的接口和依赖关系

### 工具类别
- **操作系统工具**: 文件操作、目录列表、搜索、编辑
- **Python 工具**: 依赖管理、命令执行
- **实用工具**: 任务管理和实用功能
- **Git 工具**: 仓库分析（当前已禁用）

## 主要特性

### 自主智能体系统
- **多轮迭代执行**，可配置限制（默认: 20）
- **基于工具的操作**，用于文件操作和分析
- **内存持久化**，跨会话保持
- **丰富终端输出**，包含进度追踪

### 文件操作
- **绝对路径强制性**，所有文件操作都使用绝对路径
- **文本搜索和替换**，跨文件支持
- **目录遍历和分析**
- **文件创建、编辑和移动**

### Git 集成
- **仓库克隆和分析**（通过 CLI 参数）
- **分支指定**支持
- **Git 工具暂时禁用**（使用 Daytona SDK 代替）

### 🆕 Daytona 沙盒集成
- **云端隔离环境**，提供安全的代码执行环境
- **自动环境设置**，包括 nano-code 安装和依赖管理
- **文件上传/下载**，支持本地文件处理和结果下载
- **模块化架构**，易于维护和扩展
- **安全配置管理**，API 密钥通过环境变量管理

## 开发指南

### 代码风格
- 遵循 **PEP 8** 风格指南
- 所有函数和方法都使用 **类型提示**
- 所有工具操作都实现 **async/await**
- 专门使用 **绝对路径**（不使用相对路径）
- 所有操作中的行号都是 **基于 1 的**

### 工具开发
- 继承 `agent_tool/base.py` 中的基础工具类
- 在 `agent_tool/tools.py` 中注册新工具
- 对工具参数使用 **架构验证**
- 返回包含 `for_llm` 和 `for_human` 格式的结构化结果

### 测试标准
- 所有工具都必须在 `tests/` 中有相应的测试文件
- 使用 **pytest** 并支持异步（`pytest-asyncio`）
- 测试成功和错误两种情况
- 验证工具参数的架构符合性

### 错误处理
- 文件操作始终使用 try/catch 块
- 提供有意义的错误消息
- 使用会话日志记录器适当记录错误
- 优雅地失败并提供信息反馈

## 配置

### 环境变量
- `OPENAI_API_KEY` - OpenAI API 密钥（必需）
- `LLM_BASE_URL` - LLM API 基础 URL（可选，默认：https://api.openai.com/v1）
- `DAYTONA_API_KEY` - Daytona API 密钥（Daytona 代理需要）
- 通过 CLI 或会话配置工作目录
- 内存和会话数据存储在会话检查点中

### 🆕 配置文件支持
- `~/.nano_code/config.json` - LLM API 配置文件
  ```json
  {
    "llm_api_key": "your-api-key",
    "llm_base_url": "https://api.openai.com/v1"
  }
  ```

### CLI 参数 (智能模式)
- `--user-input` / `-u`: 用户输入 - Agent自动分析并选择工具（必需）
- `--working-dir`: 工作目录（默认: 当前目录）

## 会话管理

### 内存系统
- **基于会话的内存**，用于上下文保持
- **检查点保存**，任务完成后执行
- **工作环境**追踪
- **成本追踪**，用于 LLM 使用情况

### 执行流程
1. **任务初始化**，包含输入验证
2. **消息构建**，包含文件上下文
3. **自主执行循环**，包含工具调用
4. **结果编译**和日志记录
5. **会话检查点**保存

## 常用工作流程

### 基本任务执行 (智能模式)
```bash
# 智能文件分析 - Agent自动识别文件
nanocode1 --user-input "分析并总结src/main.py的代码"

# 智能多文件处理 - Agent自动处理多个文件
nanocode1 --user-input "重构module1.py和module2.py的代码结构"

# 智能仓库分析 - Agent自动克隆和分析
nanocode1 --user-input "分析https://github.com/user/repo并生成文档"
```

### 开发工作流程
1. **创建虚拟环境**并安装依赖
2. **运行现有测试**以确保基线功能
3. **实现新功能**，遵循基于工具的架构
4. **为新功能编写全面测试**
5. **使用真实场景测试 nanocode1 CLI**
6. **格式化代码并运行质量检查**

### 测试新工具
```bash
# 测试特定工具功能
pytest tests/test_new_tool.py -v

# 智能测试工具集成 - Agent自动识别测试场景
nanocode1 --user-input "测试新工具功能 使用test_input.py作为输入"

# 覆盖率报告
pytest --cov=nanocode1 --cov-report=html
```

## 安全指南

### 文件操作
- **验证所有文件路径**在操作之前
- **仅使用绝对路径**以防止目录遍历
- **检查文件权限**在读/写操作之前
- **处理用户输入时清理文件内容**

### API 使用
- **保护 OpenAI API 密钥**在环境变量中
- **监控令牌使用**以防止过度成本
- **验证工具架构**以防止格式错误的请求
- **记录工具执行**用于调试和审计

## 最佳实践

### 工具开发
- 设计工具做到 **原子化和专注**
- 使用 **描述性名称**和全面文档
- 实现 **正确的错误处理**，包含特定消息
- 在集成之前 **独立测试工具**

### 🆕 模块化架构最佳实践
- **单一职责原则**: 每个模块只负责一个特定功能
- **依赖注入**: 通过构造函数传递依赖，而非硬编码
- **配置外部化**: 所有配置通过环境变量或配置文件管理
- **接口一致性**: 保持向后兼容的 API 接口
- **错误处理**: 每个模块都有完善的异常处理机制
- **文档完整**: 每个模块都有清晰的文档说明

### 智能体交互
- 提供 **清晰的任务描述**以获得更好结果
- 尽可能使用 **具体的文件路径**
- 根据任务复杂性设置 **适当的迭代限制**
- 查看 **执行日志**以进行调试和优化

### 性能优化
- 在可能的情况下 **批量工具调用**以提高效率
- **限制文件读取**仅包含必要内容
- **使用分页**对大文件使用 offset/limit
- 在会话内存中适当 **缓存结果**

## 故障排除

### 常见问题
- **路径解析错误**: 确保使用绝对路径
- **权限拒绝**: 检查文件和目录权限
- **工具执行失败**: 查看工具架构和参数
- **内存问题**: 增加迭代限制或优化工具使用

### 调试模式
- 使用 **丰富控制台输出**获得详细执行日志
- 检查 **会话检查点**的状态持久化
- 在执行摘要中查看 **工具执行日志**
- 监控 **令牌使用**和成本追踪

### 测试问题
- 确保安装 **pytest-asyncio** 用于异步测试
- 在测试装置中使用 **绝对路径**
- 适当 **模拟外部依赖**
- 检查工具参数的 **架构验证**