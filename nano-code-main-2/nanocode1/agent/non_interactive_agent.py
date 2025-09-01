import asyncio
import json
import os
import time
from typing import List, Dict, Any
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown as M

from ..core.session import Session
from ..llm import llm_complete
from ..agent_tool.tools import OS_TOOLS, UTIL_TOOLS, PYTHON_TOOLS, GIT_TOOLS
from ..utils.logger import AIConsoleLogger
from ..prompts import (
    SYSTEM_PROMPT, RAW_ANALYSIS_PROMPT, Code_analysis_prompt, Data_anlaysis_prompt, 
    File_analysis_prompt, Graph_analysis_prompt
)
from ..models.dissertation_plan import DissertationPlan
from ..models.output_format import ReportModel, ImageArtifact, TableArtifact, CodeArtifact, FileArtifact

# 产出artifact会用到的工具（模块级常量，避免重复定义）
ARTIFACT_TOOLS = ["create_file", "write_file", "RunCommand", "render_mermaid"]

# 简化的任务结果管理器
class TaskResultManager:
    @staticmethod
    def create_fully_completed_result(phase_name: str, output_path: str, agent_output, iteration: int) -> Dict[str, Any]:
        return {
            "status": "completed",
            "phase": phase_name,
            "output_path": output_path,
            "iteration": iteration,
            "message": f"任务完成: {phase_name}",
            "agent_output": agent_output
        }

# 控制台输出捕获器
class ConsoleOutputCapture:
    def __init__(self, console: Console):
        self.console = console
        self.captured_output = []
    
    def capture_print(self, content: str):
        self.captured_output.append(content)
        self.console.print(content)


class NonInteractiveAgent:
    
    def __init__(self, session: Session, console: Console = None):
        self.session = session
        self.console = console or Console()
        self.all_tools = OS_TOOLS.merge(UTIL_TOOLS).merge(PYTHON_TOOLS).merge(GIT_TOOLS)
        self.execution_log = []
        
        # 使用专门的管理器
        self.console_capture = ConsoleOutputCapture(self.console)
        
        # TODO列表管理
        self.session.todo_list = []
        
        # 文件扫描状态管理
        self._recent_files_scanned = False
    
    
    async def execute_task(self, dissertation_plan: DissertationPlan) -> Dict[str, Any]: 
        """
        执行任务的主流程

        Args:
            dissertation_plan (DissertationPlan): 任务计划

        Returns:
            Dict[str, Any]: 任务执行结果
        """
        task_prompt = self._convert_dissertation_plan_to_prompt(dissertation_plan)
        
        # 第一阶段：执行当前任务（不管是否需要搜索）
        messages = [{"role": "user", "content": task_prompt}]
        
        # 根据 is_first_time 选择使用的system prompt
        if dissertation_plan.is_first_time:
            selected_prompt = RAW_ANALYSIS_PROMPT
            phase_name = "first_time_analysis"
        else:
            selected_prompt = SYSTEM_PROMPT
            phase_name = "task_execution"
        
        
        self.console.print(f"🚀 开始执行阶段: {phase_name}")
        
        # 执行当前阶段的任务
        result = await self._autonomous_execution_loop(
            messages,
            system_prompt=selected_prompt
        )
        
        # 构建当前阶段的输出
        agent_output = await self._build_agent_output(
            result.get("final_message", ""),
            result.get("execution_log", []),
            is_first_time=dissertation_plan.is_first_time
        )
        
        # 统一输出文件名
        output_filename = "agent_output.json"
        output_path = f"{self.session.working_dir}/{output_filename}"
        agent_output.save_json(output_path)
        
        self.console.print(f"✅ {phase_name} 阶段完成")
        
        # 直接返回任务完成结果（搜索判断逻辑已移除）
        return TaskResultManager.create_fully_completed_result(
            phase_name, output_path, agent_output, result.get("iteration", 0)
        )
  
    def _convert_dissertation_plan_to_prompt(self, plan: DissertationPlan) -> str: 
        """
        把json中的任务要求转换为llm的输入；若存在外部搜索资料（agent_communicate.response），会注入到提示中。

        Args:
            plan (DissertationPlan): 任务计划

        Returns:
            str: llm的输入
        """
        prompt_parts = []
        
        # 代码仓库分析部分
        if plan.experimental_requirements.code_repository_review:
            repo = plan.experimental_requirements.code_repository_review
            prompt_parts.extend([
                "### 代码仓库分析",
                f"- 仓库地址：{repo.url}",
                f"- 描述：{repo.description}",
                f"- 分析重点：{', '.join(repo.analysis_focus)}",
                ""
            ])
        
        # 实验任务部分
        if plan.experimental_requirements.reproduction_tasks:
            prompt_parts.append("### 需要完成的实验任务")
            for i, task in enumerate(plan.experimental_requirements.reproduction_tasks, 1):
                prompt_parts.extend([
                    f"{i}. **{task.phase}**",
                    f"   - 目标：{task.target}",
                    f"   - 方法：{task.methodology}",
                    ""
                ])
        
        # 评估要求
        if plan.experimental_requirements.critical_evaluation:
            eval_req = plan.experimental_requirements.critical_evaluation
            prompt_parts.extend([
                "### 批判性评估要求",
                f"- 失败案例研究：{eval_req.failure_case_study}",
                f"- 改进方向：{', '.join(eval_req.improvement_directions)}",
                ""
            ])
        
        # 相关资源
        if plan.urls:
            prompt_parts.append("### 相关资源")
            for url_info in plan.urls:
                prompt_parts.append(f"- {url_info.url}: {url_info.description}")
            prompt_parts.append("")

        # 外部搜索资料补充（仅当存在非空 response 时注入）
        try:
            comms = getattr(plan, "agent_communicate", None)
            if comms:
                enriched_lines: List[str] = []
                count = 0
                for comm in comms:
                    resp = getattr(comm, "response", None)
                    if resp and isinstance(resp, str) and resp.strip():
                        count += 1
                        # 控制长度，避免提示过长
                        resp_snippet = resp.strip()
                        if len(resp_snippet) > 3000:
                            resp_snippet = resp_snippet[:3000] + "…"
                        req_snippet = getattr(comm, "request", "")
                        if req_snippet and len(req_snippet) > 3000:
                            req_snippet = req_snippet[:3000] + "…"
                        enriched_lines.append(f"- 资料 {count}（对应需求：{req_snippet}）\n  {resp_snippet}")
                        if count >= 5:
                            break
                if enriched_lines:
                    prompt_parts.append("### 外部搜索资料补充（用于提高完成质量与准确性）")
                    prompt_parts.extend(enriched_lines)
                    prompt_parts.append("")
        except Exception:
            pass
        
        return "\n".join(prompt_parts)
    
    async def _build_agent_output(self, report: str, execution_log: List[dict], is_first_time: bool = False) -> ReportModel: 
        """
        按照规定格式输出，智能选择最合适的附件类型
        
        当 is_first_time=True 时，将生成的 markdown 内容保存在 report 字段中，
        不将 .md 文件作为 artifact 返回。

        Args:
            report (str): 报告内容
            execution_log (List[dict]): 执行日志
            is_first_time (bool): 是否为第一次分析

        Returns:
            ReportModel: 输出结果
        """
        artifacts = []
        processed_files = set()  # 用于去重的文件集合
        
        # 收集执行过程中新创建的文件作为附件
        for log_entry in execution_log:
            tool_name = log_entry.get("tool", "")

            if tool_name in ARTIFACT_TOOLS:
                new_file_artifacts = await self._detect_new_files(log_entry)
                
                # 去重处理：只添加未处理过的文件
                for artifact in new_file_artifacts:
                    file_identifier = self._get_artifact_file_identifier(artifact)
                    if file_identifier not in processed_files:
                        processed_files.add(file_identifier)
                        
                        # 第一次分析时，跳过 .md 文件作为 artifact
                        # 因为 markdown 内容已经在 report 字段中
                        if is_first_time and hasattr(artifact, 'title') and artifact.title.endswith('.md'):
                            continue
                            
                        artifacts.append(artifact)
        
        return ReportModel(
            report=report,
            artifacts=artifacts
        )
    
    def _get_artifact_file_identifier(self, artifact) -> str:
        """获取artifact的唯一标识符用于去重"""
        return getattr(artifact, 'title', '')
    
    async def _detect_new_files(self, log_entry: dict) -> list:
        """检测工具执行后新创建的文件并创建对应artifacts"""
        artifacts = []
        
        # 从日志中获取执行前后的文件时间戳信息
        file_changes = log_entry.get("file_changes", {})
        new_files = file_changes.get("created", [])
        
        # 如果没有文件变化信息，回退到扫描工作目录（但只扫描一次）
        if not new_files:
            if not hasattr(self, '_recent_files_scanned') or not self._recent_files_scanned:
                new_files = self._scan_recent_files()
                self._recent_files_scanned = True
            else:
                new_files = []
        
        for file_path in new_files:
            if not Path(file_path).exists():
                continue
                
            # 获取或生成LLM分析结果
            analysis = log_entry.get("llm_analysis", "")
            
            # 如果没有现有分析，为需要分析的文件类型生成分析
            if not analysis:
                file_extension = Path(file_path).suffix.lower()
                if file_extension in ['.png', '.csv', '.py']:
                    try:
                        # 读取文件内容用于分析
                        content = ""
                        if file_extension == '.py':
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                        analysis = await self._analyze_generated_content(file_path, content)
                    except Exception as e:
                        analysis = f"无法分析文件: {str(e)}"
            
            artifact = self._create_artifact_by_extension(file_path, analysis)
            if artifact:
                artifacts.append(artifact)
        
        return artifacts
    
    def _scan_recent_files(self) -> list[str]:
        """扫描工作目录中最近创建的有意义文件"""
        current_time = time.time()
        recent_files = set()  # 去重
        
        # 只关注核心文件格式
        target_extensions = {'.csv', '.py', '.png', '.md', '.mmd'}
        
        try:
            for root, dirs, files in os.walk(self.session.working_dir):
                # 跳过缓存目录
                dirs[:] = [d for d in dirs if not d.startswith(('__pycache__', '.pytest_cache', '.git', '.cache'))]
                
                for file in files:
                    # 只处理目标扩展名的文件
                    if not any(file.lower().endswith(ext) for ext in target_extensions):
                        continue
                        
                    file_path = os.path.join(root, file)
                    
                    if not self.session.ignore_path(file_path):
                        # 检查文件是否在最近5分钟内创建
                        if current_time - os.path.getctime(file_path) < 300:
                            recent_files.add(file_path)
        except Exception:
            pass
            
        return list(recent_files)
    
    def _create_artifact_by_extension(self, file_path: str, analysis: str = ""):
        """根据文件扩展名创建对应的artifact"""
        try:
            file_extension = Path(file_path).suffix.lower()
            file_name = Path(file_path).name
            
            if file_extension == '.png':
                # 创建临时实例来调用image_to_base64方法
                return ImageArtifact(
                    image=file_path,
                    title=file_name,
                    description=analysis  # 完全依赖LLM分析
                )
            
            elif file_extension == '.csv':
                return TableArtifact(
                    table=file_path,
                    title=file_name,
                    description=analysis  # 完全依赖LLM分析
                )
            
            elif file_extension == '.py':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return CodeArtifact(
                        code=content,
                        title=file_name,
                        description=analysis  # 完全依赖LLM分析
                    )
                except Exception:
                    pass
            
            elif file_extension in ['.md', '.mmd']:
                # 为Markdown文件提供基本描述
                if not analysis:
                    analysis = f"Markdown文档: {file_name}"
                return FileArtifact(
                    file=file_path,
                    title=file_name,
                    description=analysis
                )
                
        except Exception:
            return None
    
    def _get_formatted_memories(self) -> str:
        code_memories = self.session.get_memory()
        if code_memories:
            return f"Below are some working memories:\n{code_memories}"
        else:
            return ""
    
    def _get_formatted_system_prompt(self) -> str:
        return SYSTEM_PROMPT.format(
            working_dir=self.session.working_dir,
            todo_status=self._get_todo_status(),
            memories=self._get_formatted_memories()
        )
    
    def _get_todo_status(self) -> str:
        """获取TODO状态文本"""
        if not hasattr(self.session, 'todo_list') or not self.session.todo_list:
            return "TODO Status: No TODO list created yet. Create one at the start!"
        
        total = len(self.session.todo_list)
        completed = sum(1 for item in self.session.todo_list if item.status == "completed")
        completion_rate = (completed / total) * 100 if total > 0 else 0
        
        status_lines = [f"TODO Progress: {completed}/{total} completed ({completion_rate:.0f}%)"]
        
        for item in self.session.todo_list:
            status_icon = "✅" if item.status == "completed" else "🔄" if item.status == "in_progress" else "⏳"
            status_lines.append(f"{status_icon} [{item.id}] {item.description}")
        
        return "\n".join(status_lines)
    
    def _is_todo_complete(self) -> bool:
        """检查TODO是否全部完成"""
        if not hasattr(self.session, 'todo_list') or not self.session.todo_list:
            return True  # 没有TODO列表视为完成
        
        return all(item.status == "completed" for item in self.session.todo_list)
    
    def _get_incomplete_todos(self) -> str:
        """获取未完成TODO项目的描述"""
        if not hasattr(self.session, 'todo_list') or not self.session.todo_list:
            return "No TODO items"
        
        incomplete = [item for item in self.session.todo_list if item.status != "completed"]
        if not incomplete:
            return "All TODO items completed"
        
        lines = []
        for item in incomplete:
            status_icon = "🔄" if item.status == "in_progress" else "⏳"
            lines.append(f"{status_icon} [{item.id}] {item.description}")
        
        return "\n".join(lines)


    async def _analyze_generated_content(self, file_path: str, content: str) -> str: 
        """
        分析生成的内容，根据文件类型选择不同prompt，output format中的description

        Args:
            file_path (str): 文件路径
            content (str): 文件内容

        Returns:
            content: 分析结果
        """
        file_extension = Path(file_path).suffix.lower()
        file_name = Path(file_path).name
        
        # 根据文件类型定制分析提示
        if file_extension in ['.png']:
            analysis_prompt = Graph_analysis_prompt.format(file_name = file_name, file_path = file_path)

        elif file_extension in ['.csv', ]:
            analysis_prompt = Data_anlaysis_prompt.format(file_name = file_name, file_path = file_path)
        elif file_extension in ['.py']:
            analysis_prompt = Code_analysis_prompt.format(file_name = file_name, content = content)
        else:
            analysis_prompt = File_analysis_prompt.format(file_name = file_name, content = content)     
        try:
            analysis_response = await llm_complete(
                self.session,
                self.session.working_env.llm_main_model,
                [{"role": "user", "content": analysis_prompt}],
                system_prompt=self._get_formatted_system_prompt()
            )
            return analysis_response.choices[0].message.content
        except Exception as e:
            return f"分析生成时出错: {str(e)}"
    
    
    async def _autonomous_execution_loop(
        self, 
        messages: List[dict], 
        system_prompt: str
        ) -> Dict[str, Any]:
        """
        自动执行循环。

        Args:
            messages (List[dict]): 消息历史
            system_prompt (str): 

        Returns:
            Dict[str, Any]: 任务执行结果，包含状态、最终消息、迭代次数和执行日志。
        """
        iteration = 0
        
        # 获取项目内存
        memories = self._get_formatted_memories()

        
        while True:
            iteration += 1
            self.console.print(f"🔄 执行轮次 {iteration}")
            
            # 调用LLM
            response = await llm_complete(
                self.session,
                self.session.working_env.llm_main_model,
                messages,
                system_prompt=system_prompt.format(
                    working_dir=self.session.working_dir,
                    todo_status=self._get_todo_status(),
                    memories=memories
                ),
                tools=self.all_tools.get_schemas(),
            )
            
            choice = response.choices[0]
            
            if choice.finish_reason != "tool_calls":
                # 检查TODO完成状态
                todo_complete = self._is_todo_complete()
                
                if todo_complete:
                    return {
                        "status": "completed",
                        "final_message": choice.message.content,
                        "iteration": iteration,
                        "execution_log": self.execution_log
                    }
                else:
                    # TODO未完成，继续执行
                    incomplete_items = self._get_incomplete_todos()
                    
                    # 向消息历史添加提醒
                    reminder = f"""Your TODO list is not yet complete. You cannot finish until all items are completed.

Incomplete items:
{incomplete_items}

Please continue using tools to complete these remaining tasks. Use update_todo_status to mark items as completed when done."""
                    
                    messages.append({"role": "assistant", "content": choice.message.content})
                    messages.append({"role": "user", "content": reminder})
                    continue
            
            # 新增：即使在调用工具，也检查TODO状态
            elif iteration > 60 and self._is_todo_complete():
                self.console.print("✅ TODO完成，强制结束任务（防止无限循环）")
                # 不直接return，而是设置完成状态让循环正常退出
                # 这样可以确保execute_task中的ReportModel构建代码能够执行
                # 使用LLM的最后输出作为最终报告内容
                final_message = choice.message.content if choice.message.content else "任务已完成，所有TODO项目已完成"
                break
            
            # 显示AI的思考过程
            if choice.message.content:
                # 转义Rich Console标记以避免解析错误
                safe_content = choice.message.content.replace('[', '\\[').replace(']', '\\]')
                self.console.print(Panel(M(safe_content), title="Assistant"))
            
            # 添加助手消息
            messages.append(choice.message.model_dump())

            
            # 执行工具调用
            tool_calls = [
                t for t in choice.message.tool_calls
                if self.all_tools.has_tool(t.function.name)
            ]
            
            # 工具调用信息
            for t in tool_calls:
                self.console.print(f"🔧 [bold blue]调用工具:[/bold blue] {t.function.name}")
                try:
                    args = json.loads(t.function.arguments)
                    self.console.print(f"📝 [bold green]参数:[/bold green] {json.dumps(args, indent=2, ensure_ascii=False)}")
                except json.JSONDecodeError:
                    self.console.print(f"📝 [bold yellow]参数 (原始):[/bold yellow] {t.function.arguments}")
                self.console.print("─" * 50)
            
            # 批量执行工具
            tasks = [
                self.all_tools.execute(
                    self.session, t.function.name, json.loads(t.function.arguments)
                )
                for t in tool_calls
            ]
            
            results = await asyncio.gather(*tasks)
            
            # 添加工具结果到消息历史并分析生成的内容
            for t, r in zip(tool_calls, results):
                messages.append({
                    "role": "tool",
                    "tool_call_id": t.id,
                    "content": r.for_llm,
                })
                
                # 创建基础执行日志
                log_entry = {
                    "iteration": iteration,
                    "tool": t.function.name,
                    "args": json.loads(t.function.arguments),
                    "result": r.for_human
                }
                
                # 如果是artifact创建工具，请求LLM对生成内容进行分析
                if any(tool.lower() in t.function.name.lower() for tool in ARTIFACT_TOOLS):
                    args = log_entry.get("args", {})
                    file_path = args.get("file_path", "")
                    content = args.get("content", "")
                    
                    if file_path and content:
                        file_extension = Path(file_path).suffix.lower()
                        # 只为需要深度分析的文件类型生成LLM分析
                        if file_extension in ['.py', '.csv']:
                            analysis = await self._analyze_generated_content(file_path, content)
                            log_entry["llm_analysis"] = analysis
                        elif file_extension == '.png':
                            # PNG文件使用文件路径进行分析（不需要content）
                            analysis = await self._analyze_generated_content(file_path, "")
                            log_entry["llm_analysis"] = analysis
                
                self.execution_log.append(log_entry)
        
        # 循环结束后，返回完成状态（处理break情况）
        # 确保final_message总是有合适的值
        if 'final_message' not in locals():
            final_message = "任务执行完成，所有TODO项目已完成"
        
        return {
            "status": "completed",
            "final_message": final_message,
            "iteration": iteration,
            "execution_log": self.execution_log
        }


async def run_intelligent_task(dissertation_plan: DissertationPlan, working_dir: str = None): 
    """
    外层调用

    Args:
        dissertation_plan (DissertationPlan): 任务计划，包含任务描述和执行步骤。
        working_dir (str, optional): 工作目录，默认当前目录。

    Returns:
        Dict[str, Any]: 任务执行结果，包含状态、最终消息、迭代次数和执行日志。
    """
    console = Console()
    
    # 设置工作目录
    if working_dir is None:
        working_dir = os.getcwd()
    
    # 创建会话
    session = Session(working_dir=working_dir, logger=AIConsoleLogger(console))
    
    agent = NonInteractiveAgent(session, console)
    
    try:
        console.print("🚀 Agent开始执行任务...")
        
        result = await agent.execute_task(dissertation_plan)
        
        console.print(Panel(
            f"状态: {result['status']}\n"
            f"执行阶段: {result.get('phase', 'unknown')}\n"
            f"使用轮次: {result.get('iteration', 0)}\n"
            f"执行步骤: {len(agent.execution_log)} 个",
            title="📊 任务执行摘要",
            border_style="green" if result['status'] == 'completed' else "yellow"
        ))
        
        return result
    finally:
        # 保存检查点
        session.save_checkpoints()
