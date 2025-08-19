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
from ..agent_tool.tools import OS_TOOLS, UTIL_TOOLS, PYTHON_TOOLS, GIT_TOOLS
from ..utils.logger import AIConsoleLogger
from ..prompts import SYSTEM_PROMPT, RAW_ANALYSIS_PROMPT
from ..models.dissertation_plan import DissertationPlan


class NonInteractiveAgent:
    
    def __init__(self, session: Session, console: Console = None):
        self.session = session
        self.console = console or Console()
        self.all_tools = OS_TOOLS.merge(UTIL_TOOLS).merge(PYTHON_TOOLS).merge(GIT_TOOLS)
        self.execution_log = []
    
    
    async def execute_task_intelligently(self, task_context: dict) -> Dict[str, Any]:
        input_type = task_context.get("type")
        
        if input_type == "url_analysis":
            return await self._execute_url_analysis(task_context)
        elif input_type == "json_task_execution":
            return await self._execute_json_tasks(task_context)
        else:
            raise ValueError(f"不支持的输入类型: {input_type}")
    
    
    async def _execute_url_analysis(self, task_context: dict) -> Dict[str, Any]: #分析代码仓库
        url = task_context["url"]
        
        analysis_prompt = f"请分析以下代码仓库：{url}"
        messages = [{"role": "user", "content": analysis_prompt}]
        
        result = await self._autonomous_execution_loop(
            messages, 
            analysis_prompt,
            system_prompt=RAW_ANALYSIS_PROMPT
        )
        
        return {
            "status": "completed",
            "phase": "url_analysis",
            "url": url,
            "analysis_document": result.get("final_message", ""),
            "iteration": result.get("iteration", 0),
            "execution_log": result.get("execution_log", [])
        }
    
    
    async def _execute_json_tasks(self, task_context: dict) -> Dict[str, Any]:
        dissertation_plan = task_context["dissertation_plan"]
        
        task_prompt = self._convert_dissertation_plan_to_prompt(dissertation_plan)
        messages = [{"role": "user", "content": task_prompt}]
        
        result = await self._autonomous_execution_loop(
            messages,
            task_prompt,
            system_prompt=SYSTEM_PROMPT
        )
        
        return {
            "status": "completed",
            "phase": "json_task_execution", 
            "task_results": result.get("final_message", ""),
            "iteration": result.get("iteration", 0),
            "execution_log": result.get("execution_log", [])
        }
    
    
    def _convert_dissertation_plan_to_prompt(self, plan: DissertationPlan) -> str:
        """将DissertationPlan转换为Agent可执行的提示."""
        prompt_parts = [
            f"# 学术研究任务：{plan.dissertation_title}",
            "",
            "## 研究背景",
            f"文献主题：{', '.join(plan.literature_topic)}",
            "",
            "## 需要执行的研究内容",
        ]
        
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
        
        # 执行指导
        prompt_parts.extend([
            "## 执行要求",
            "请作为专业的研究助手，智能地分析上述研究计划，并：",
            "1. 自主决定最佳的执行顺序和方法",
            "2. 灵活使用可用的工具完成各项研究任务", 
            "3. 根据实际情况调整研究策略",
            "4. 生成高质量的研究输出和文档",
            "",
            "你有完全的自主权来决定如何最好地完成这个研究计划。"
        ])
        
        return "\n".join(prompt_parts)
    
    async def _autonomous_execution_loop(
        self, 
        messages: List[dict], 
        prompt_content: str, 
        system_prompt: str
    ) -> Dict[str, Any]:
        """自主执行循环的核心逻辑."""
        iteration = 0
        
        # 获取项目内存
        code_memories = self.session.get_memory()
        memories = f"""Below are some working memories:
{code_memories}""" if code_memories else ""
        
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
        


async def run_intelligent_task(task_context: dict, working_dir: str = None):
    """新的统一任务执行入口函数."""
    console = Console()
    
    # 设置工作目录
    if working_dir is None:
        working_dir = os.getcwd()
    
    # 创建会话
    session = Session(working_dir=working_dir, logger=AIConsoleLogger(console))
    
    agent = NonInteractiveAgent(session, console)
    
    try:
        console.print("🚀 Agent开始执行任务...")
        
        result = await agent.execute_task_intelligently(task_context)
        
        console.print(Panel(
            f"状态: {result['status']}\n"
            f"执行阶段: {result.get('phase', 'unknown')}\n"
            f"使用轮次: {result.get('iteration', 0)}\n"
            f"执行步骤: {len(result.get('execution_log', []))} 个",
            title="📊 任务执行摘要",
            border_style="green" if result['status'] == 'completed' else "yellow"
        ))
        
        return result
        
    finally:
        # 保存检查点
        session.save_checkpoints()