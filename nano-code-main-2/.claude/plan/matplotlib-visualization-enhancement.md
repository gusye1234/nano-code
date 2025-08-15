# matplotlib 可视化增强任务

## 任务上下文
为 nanocode1 项目的 URL 分析功能添加 matplotlib 可视化支持，生成项目结构图和执行流程图，并且与分析的md文档放在一起，要求图片清晰美观，支持保存为PNG 格式。

## 选定方案
方案 3：混合方案 - 创建基础模板库 + 增强 prompt 指令

## 执行计划
1. 分析现有实现状况
2. 创建基础可视化模板库 (`nanocode1/utils/visualization_templates.py`)
3. 增强 RAW_ANALYSIS_PROMPT
4. 优化依赖管理配置
5. 测试验证流程
6. 文档更新

## 成功标准
- Agent 能稳定生成高质量的 matplotlib 代码
- 图片清晰美观（DPI=300，统一样式）
- 图片与 MD 文档保存在相同位置
- 完整的错误处理和调试信息