import asyncio
import json
import os
from typing import List, Dict, Any
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown as M

from ..core.session import Session
from ..llm import llm_complete
from ..agent_tool.tools import OS_TOOLS, UTIL_TOOLS, PYTHON_TOOLS
from ..utils.logger import AIConsoleLogger


class NonInteractiveAgent:
    
    def __init__(self, session: Session, console: Console = None):
        self.session = session
        self.console = console or Console()
        self.all_tools = OS_TOOLS.merge(UTIL_TOOLS).merge(PYTHON_TOOLS)
        self.execution_log = []
    
    async def execute_task(self, task_description: str, input_files: List[str] = None, max_iterations: int = 20) -> Dict[str, Any]:#执行要求任务
        self.console.print(f"🎯 开始执行任务: {task_description}")
        
        # 验证输入文件
        if input_files:
            validated_files = self._validate_input_files(input_files)
        else:
            validated_files = []
        
        # 根据任务构建初始prompt
        messages = self._build_initial_messages(task_description, validated_files)
        
        # 自主执行循环
        result = await self._autonomous_execution_loop(messages, max_iterations)
        
        return result
    
    def _validate_input_files(self, file_paths: List[str]) -> List[str]: #分析目标文件路径是否存在
        validated = []
        for path in file_paths:
            file_path = Path(path)
            if file_path.exists():
                validated.append(str(file_path.absolute()))
                self.console.print(f"✅ 文件路径为: {path}")
            else:
                self.console.print(f"⚠️  文件不存在: {path}")
        return validated
    
    def _build_initial_messages(self, task_description: str, validated_files: List[str]) -> List[dict]: #初始信息 user_message
        file_list = "\n".join([f"- {f}" for f in validated_files]) if validated_files else "无输入文件"
        
        user_message = f"""请执行以下任务:

        Task: {task_description}

        Available Files:
        {file_list}

        请自主完成整个任务，包括:
        1. 分析输入文件（如果有）
        2. 执行必要的处理
        3. 生成结果文件
        4. 提供完整的总结报告

        开始执行任务。不要询问任何问题，直接开始执行。
        """
        
        return [{"role": "user", "content": user_message}]
    
    async def _autonomous_execution_loop(self, messages: List[dict], max_iterations: int) -> Dict[str, Any]: #自动执行循环
        iteration = 0
        
        # 获取项目内存
        code_memories = self.session.get_memory()
        memories = f"""Below are some working memories:
{code_memories}""" if code_memories else ""
        
        while iteration < max_iterations:
            iteration += 1
            self.console.print(f"🔄 执行轮次 {iteration}/{max_iterations}")
            
            # 调用LLM
            response = await llm_complete(
                self.session,
                self.session.working_env.llm_main_model,
                messages,
                system_prompt=f"""You are an autonomous AI assistant designed to complete tasks using tools.
Your primary goal is to achieve the user's objective by planning and executing a series of tool calls.
Your current working directory is {self.session.working_dir}.

There are few rules:
- Always use absolute path.
- Line number is 1-based.
- Act autonomously. Formulate a plan and execute it without asking for my approval or for more details.
- If a step in your plan fails, analyze the error, revise the plan, and retry.
- Always examine if you have accomplished the tasks before you stop, if not, continue to try. If yes, report to me with your recap.
- Always tell me your brief plan before you call tools, but don't wait for my approval.
- The files you read before maybe updated, make sure you read the latest version before you edit them.
- When task is completed, provide a comprehensive summary of what was accomplished.
{memories}
""",
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
        
        # 达到最大轮次
        return {
            "status": "max_iterations_reached",
            "final_message": "任务未在规定轮次内完成",
            "iteration": iteration,
            "execution_log": self.execution_log
        }


async def run_non_interactive_task(task_description: str, input_files: List[str] = None, working_dir: str = None, max_iterations: int = 20):
    
    console = Console()
    
    # 设置工作目录
    if working_dir is None:
        working_dir = os.getcwd()
    
    # 创建会话
    session = Session(working_dir=working_dir, logger=AIConsoleLogger(console))
    
    agent = NonInteractiveAgent(session, console)
    
    try:
        # 执行任务
        result = await agent.execute_task(task_description, input_files, max_iterations)
        
        # 显示结果摘要
        console.print(Panel(
            f"状态: {result['status']}\n"
            f"使用轮次: {result['iteration']}/{max_iterations}\n"
            f"执行步骤: {len(result['execution_log'])} 个",
            title="📊 任务执行摘要",
            border_style="green" if result['status'] == 'completed' else "yellow"
        ))
        
        return result
        
    finally:
        # 保存检查点
        session.save_checkpoints()