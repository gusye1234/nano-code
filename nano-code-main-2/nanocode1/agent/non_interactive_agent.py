import asyncio
import json
import os
import re
from typing import List, Dict, Any
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown as M

from ..core.session import Session
from ..llm import llm_complete
from ..agent_tool.tools import OS_TOOLS, UTIL_TOOLS, PYTHON_TOOLS, GIT_TOOLS
from ..utils.logger import AIConsoleLogger
from ..prompts import SYSTEM_PROMPT, RAW_ANALYSIS_PROMPT


class NonInteractiveAgent:
    
    def __init__(self, session: Session, console: Console = None):
        self.session = session
        self.console = console or Console()
        self.all_tools = OS_TOOLS.merge(UTIL_TOOLS).merge(PYTHON_TOOLS).merge(GIT_TOOLS)
        self.execution_log = []
    
    
    async def execute_task_intelligently(self, task_context: dict) -> Dict[str, Any]:
        final_task = task_context["final_task"]
        
        self.console.print(f"🧠 Agent开始智能分析任务...")
        
        # 构建智能分析的初始prompt - 让Agent自己决定使用什么工具
        messages = self._build_intelligent_messages(final_task)
        
        # 自主执行循环 - 传递原始用户输入用于prompt选择
        result = await self._autonomous_execution_loop(messages, final_task)
        
        return result
    
    def _build_intelligent_messages(self, task_input: str) -> List[dict]:
        #修饰用户输入
        return [{"role": "user", "content": task_input}]
    
    def _is_pure_url_input(self, user_input: str) -> bool:
        """检测用户输入是否为单纯的URL"""
        # 去除首尾空格和换行符
        cleaned_input = user_input.strip()
        
        # URL模式匹配 - 支持http和https
        url_pattern = r'^https?://[^\s]+$'
        
        # 检查是否匹配URL模式且没有其他描述文字
        return re.match(url_pattern, cleaned_input) is not None
    
    def _validate_input_files(self, file_paths: List[str]) -> List[str]:
        validated = []
        for path in file_paths:
            file_path = Path(path)
            if file_path.exists():
                validated.append(str(file_path.absolute()))
                self.console.print(f"✅ 文件存在: {path}")
            else:
                self.console.print(f"⚠️  文件不存在: {path}")
        return validated
    
    
    async def _autonomous_execution_loop(self, messages: List[dict], user_input: str) -> Dict[str, Any]:
        iteration = 0
        
        # 获取项目内存
        code_memories = self.session.get_memory()
        memories = f"""Below are some working memories:
{code_memories}""" if code_memories else ""
        
        # 根据输入类型选择prompt
        if self._is_pure_url_input(user_input):
            selected_prompt = RAW_ANALYSIS_PROMPT
            self.console.print("🔍 仅输入URL，克隆项目并执行初步分析")
        else:
            selected_prompt = SYSTEM_PROMPT
            self.console.print("🧠 使用通用智能分析模式")
        
        while True:
            iteration += 1
            self.console.print(f"🔄 执行轮次 {iteration}")
            
            # 调用LLM - 使用选择的prompt
            response = await llm_complete(
                self.session,
                self.session.working_env.llm_main_model,
                messages,
                system_prompt=selected_prompt.format(
                    working_dir=self.session.working_dir,
                    memories=memories
                ),
                tools=self.all_tools.get_schemas(),
            )
            
            choice = response.choices[0]
            
            if choice.finish_reason != "tool_calls":
                self.console.print("✅ 任务执行完成")
                return {
                    "status": "completed",
                    "final_message": choice.message.content,
                    "iteration": iteration,
                    "execution_log": self.execution_log
                }
            
            # 显示AI的思考过程
            if choice.message.content:
                self.console.print(Panel(M(choice.message.content), title="Assistant"))
            
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
            
            # 添加工具结果到消息历史
            for t, r in zip(tool_calls, results):
                messages.append({
                    "role": "tool",
                    "tool_call_id": t.id,
                    "content": r.for_llm,
                })
                
                # 记录执行日志
                self.execution_log.append({
                    "iteration": iteration,
                    "tool": t.function.name,
                    "args": json.loads(t.function.arguments),
                    "result": r.for_human
                })


async def run_non_interactive_task(user_input: str, working_dir: str = None):
    console = Console()
    
    console.print(f"🧠 智能Agent启动")
    console.print(f"📝 用户输入: {user_input}")
    
    # 设置工作目录
    if working_dir is None:
        working_dir = os.getcwd()
    
    # 创建会话
    session = Session(working_dir=working_dir, logger=AIConsoleLogger(console))
    
    agent = NonInteractiveAgent(session, console)
    
    try:
        console.print("🚀 Agent开始智能分析和执行...")
        
        # 构建任务上下文 - 仅使用用户输入
        task_context = {
            "final_task": user_input,
            "input_files": [],  # Agent会自动从用户输入中识别文件
            "git_repo": None,   # Agent会自动从用户输入中识别Git URL
            "git_branch": "main"
        }
        
        result = await agent.execute_task_intelligently(task_context)
        
        console.print(Panel(
            f"状态: {result['status']}\n"
            f"使用轮次: {result['iteration']}\n"
            f"执行步骤: {len(result['execution_log'])} 个",
            title="📊 任务执行摘要",
            border_style="green" if result['status'] == 'completed' else "yellow"
        ))
        
        # created_files = session.get_created_files()
        # if created_files:
        #     created_files_log = os.path.join(working_dir, "created_files.log")
        #     with open(created_files_log, "w") as f:
        #         for file_path in created_files:
        #             f.write(f"{file_path}\n")
        #     console.print(f"📝 创建文件列表已保存: {created_files_log}")
        # # 注释：基于Session日志的文件追踪已禁用，回退到旧的文件收集方法
        
        return result
        
    finally:
        # 保存检查点
        session.save_checkpoints()