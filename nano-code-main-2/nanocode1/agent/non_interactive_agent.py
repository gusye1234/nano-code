import os
from typing import Dict, Any, Optional
from rich.console import Console

from ..core.session import Session
from ..agent_tool.tools import OS_TOOLS, UTIL_TOOLS, PYTHON_TOOLS, GIT_TOOLS
from ..utils.logger import AIConsoleLogger
from ..prompts import SYSTEM_PROMPT, RAW_ANALYSIS_PROMPT
from ..models.dissertation_plan import DissertationPlan
from ..models.output_format import ReportModel
from . import tracing
from . import prompt_builder
from . import artifacts
from . import content_analyzer
from . import reporting
from . import execution_loop


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

class NonInteractiveAgent:
    
    def __init__(self, session: Session, console: Console = None, existing_report: Optional[ReportModel] = None):
        self.session = session
        self.console = console or Console()
        self.existing_report = existing_report
        self.all_tools = OS_TOOLS.merge(UTIL_TOOLS).merge(PYTHON_TOOLS).merge(GIT_TOOLS)
        self.execution_log = []
        
        # TODO列表管理
        self.session.todo_list = []
    
    
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
        
        
        tracing.print_phase_start(self.console, phase_name)
        
        # 执行当前阶段的任务，使用新的execution_loop模块
        result = await execution_loop.run_loop(
            session=self.session,
            all_tools=self.all_tools,
            messages=messages,
            system_prompt=selected_prompt,
            console=self.console
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
        
        tracing.print_phase_complete(self.console, phase_name)
        
        # 同步执行日志到实例变量（保持向后兼容性）
        self.execution_log = result.get('execution_log', [])
        
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
        # 使用新的prompt_builder模块
        return prompt_builder.build_user_prompt(plan)
    
    async def _build_agent_output(self, report: str, execution_log: list, is_first_time: bool = False) -> ReportModel: 
        """
        按照规定格式输出，选择最合适的附件类型
        
        使用新的reporting模块构建输出

        Args:
            report (str): 报告内容
            execution_log (list): 执行日志
            is_first_time (bool): 是否为第一次分析

        Returns:
            ReportModel: 输出结果
        """
        return await reporting.build_agent_output(
            report=report,
            execution_log=execution_log,
            existing_report=self.existing_report,
            is_first_time=is_first_time,
            artifact_detector_func=self._detect_new_files
        )
    
    async def _detect_new_files(self, log_entry: dict) -> list:
        """检测工具执行后新创建的文件并创建对应artifacts"""
        # 使用新的artifacts模块
        return await artifacts.detect_new_artifacts(
            log_entry=log_entry,
            session=self.session,
            analyzer_func=self._analyze_generated_content
        )

    async def _analyze_generated_content(self, file_path: str, content: str) -> str: 
        """
        分析生成的内容，根据文件类型选择不同prompt，output format中的description

        Args:
            file_path (str): 文件路径
            content (str): 文件内容

        Returns:
            content: 分析结果
        """
        # 使用content_analyzer，传入prompt
        system_prompt = prompt_builder.build_system_prompt(self.session)
        return await content_analyzer.analyze_generated_content(
            session=self.session,
            file_path=file_path,
            content=content,
            system_prompt=system_prompt
        ) 


async def run_intelligent_task(dissertation_plan: DissertationPlan, working_dir: str = None, existing_report: Optional[ReportModel] = None): 
    """
    外层调用

    Args:
        dissertation_plan (DissertationPlan): 任务计划，包含任务描述和执行步骤。
        working_dir (str, optional): 工作目录，默认当前目录。
        existing_report (ReportModel, optional): 已有报告，用于增量添加artifacts。

    Returns:
        Dict[str, Any]: 任务执行结果，包含状态、最终消息、迭代次数和执行日志。
    """
    console = Console()
    
    # 设置工作目录
    if working_dir is None:
        working_dir = os.getcwd()
    
    # 创建会话
    session = Session(working_dir=working_dir, logger=AIConsoleLogger(console))
    
    agent = NonInteractiveAgent(session, console, existing_report)
    
    try:
        tracing.print_agent_start(console)
        
        result = await agent.execute_task(dissertation_plan)
        
        tracing.print_summary(console, result, len(agent.execution_log))
        
        return result
    finally:
        # 保存检查点
        session.save_checkpoints()
