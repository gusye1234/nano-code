# nano-code Python文件分析系统使用指南

## 🚀 系统简介

nano-code Python文件分析系统是一个专注于Python开发的自动化文件处理解决方案，让用户能够在安全的沙盒环境中分析Python项目中的代码、数据和配置文件，无需手动执行复杂的Docker命令。

### ✨ 核心特性

- **🔒 完全沙盒隔离**: 所有分析在Docker容器中进行，确保系统安全
- **📤 自动文件上传**: 放入文件夹即可自动上传到沙盒
- **📥 智能结果下载**: 退出时自动下载所有分析结果
- **🤖 AI智能分析**: 支持多种文件类型的智能分析
- **📊 丰富的可视化**: 自动生成图表和统计报告

## 📋 系统要求

### 必需环境
- **操作系统**: macOS (已测试) / Linux
- **Docker**: 正在运行的Docker服务
- **Python**: 3.8+ 
- **磁盘空间**: 至少1GB可用空间

### 验证环境
运行以下命令确认环境就绪：

```bash
# 检查Docker状态
docker --version
docker ps

# 检查Python版本
python3 --version

# 检查nano-code镜像
docker images | grep nano-code-sandbox
```

## 🛠 首次设置

### 1. 构建沙盒镜像（如未构建）

```bash
cd /Users/gengjiawei/Documents/coding/nano-code-main-2
docker build -f Dockerfile.sandbox -t nano-code-sandbox .
```

### 2. 创建工作目录

系统会自动创建，但你也可以手动准备：

```bash
mkdir -p ~/Desktop/SandboxWork/upload
mkdir -p ~/Desktop/SandboxWork/download
```

### 3. 验证安装

```bash
cd /Users/gengjiawei/Documents/coding/nano-code-main-2
python3 auto_sandbox.py --help  # 如果有帮助参数的话
```

## 📖 详细使用教程

### 🎯 标准工作流程

#### 步骤1: 准备分析文件

将需要分析的文件放入上传目录：

```bash
# 示例：分析CSV数据文件
cp ~/Documents/sales_data.csv ~/Desktop/SandboxWork/upload/

# 示例：分析Python脚本
cp ~/Projects/my_script.py ~/Desktop/SandboxWork/upload/

# 示例：分析日志文件
cp ~/Logs/system.log ~/Desktop/SandboxWork/upload/
```

**支持的文件类型**：
- Python源码: `.py`
- 数据文件: `.csv`, `.json`
- 配置文件: `.yml`, `.yaml`, `.toml`, `.ini`, `.conf`
- 文档文件: `.txt`, `.md`, `.log`

#### 步骤2: 启动系统

```bash
cd /Users/gengjiawei/Documents/coding/nano-code-main-2
python3 auto_sandbox.py
```

**预期输出**：
```
🚀 nano-code 自动化沙盒文件分析系统
=====================================

📁 工作目录已准备: /Users/gengjiawei/Desktop/SandboxWork
📤 上传目录: /Users/gengjiawei/Desktop/SandboxWork/upload
📥 下载目录: /Users/gengjiawei/Desktop/SandboxWork/download
📋 发现 2 个待分析文件

==================================================
🔍 检查沙盒容器状态...
✅ 沙盒容器运行正常
==================================================
📤 发现 2 个文件，开始批量上传...
  ✅ sales_data.csv (1.2MB)
  ✅ my_script.py (0.1MB)
📤 成功上传 2 个文件到沙盒

🎯 已上传的文件可以在nano-code中通过以下路径访问:
   📄 /sandbox/input/sales_data.csv
   📄 /sandbox/input/my_script.py
```

#### 步骤3: AI交互分析

系统启动nano-code后，你可以与AI助手对话：

**示例对话**：
```
User: 请分析 /sandbox/input/sales_data.csv 文件，生成基础统计信息