import os
import tempfile
import json
from pathlib import Path
from typing import Optional, Union

from nanocode1.models import ReportModel
from nanocode1.models.dissertation_plan import DissertationPlan, AgentCommunication
from nanocode1.Search.decision_runner import run_decision
from nanocode1.agent.non_interactive_agent import run_intelligent_task
from nanocode1.core.session import Session
from nanocode1.utils.logger import AIConsoleLogger

# 定义返回类型别名
ReportOrPlan = Union[ReportModel, DissertationPlan]


class Coding_agent:
    def __init__(self, working_dir: Optional[str] = None):
        """初始化Coding Agent
        
        Args:
            working_dir: 工作目录，如果为None则使用当前目录
        """
        self.working_dir = working_dir or os.getcwd()
        self.logger = AIConsoleLogger()
        
    async def generate_report(self, dissertation_plan: DissertationPlan) -> ReportOrPlan:
        """
        生成报告的主要方法，实现完整的workflow
        
        Args:
            dissertation_plan: 论文计划
            
        Returns:
            ReportOrPlan: 根据情况返回ReportModel或DissertationPlan
                - 如果需要搜索: 返回包含agent_communicate的DissertationPlan
                - 如果完成分析: 返回ReportModel
        """
        try:
            # 1. 检查是否为第一次分析
            if dissertation_plan.is_first_time:
                self.logger.info("workflow", "检测到第一次分析，直接进入coding agent执行")
                reportorplan = await self._execute_coding_agent(dissertation_plan, is_first_time=True)
                return reportorplan
            
            # 2. 检查是否已有完整的搜索响应
            if (hasattr(dissertation_plan, 'agent_communicate') and 
                dissertation_plan.agent_communicate and 
                all(comm.response != "" for comm in dissertation_plan.agent_communicate)):
                self.logger.info("workflow", "检测到完整搜索响应，直接执行coding agent")
                reportorplan = await self._execute_coding_agent(dissertation_plan, is_first_time=False)
                return reportorplan
            
            # 3. 非第一次分析且无完整搜索响应，进行搜索判断
            self.logger.info("workflow", "开始搜索需求判断")
            updated_plan = await self._run_search_decision(dissertation_plan)
            
            # 4. 检查搜索判断结果
            if updated_plan.agent_communicate and any(comm.response == "" for comm in updated_plan.agent_communicate):
                self.logger.info("workflow", "检测到需要搜索，返回带搜索请求的计划")
                # 返回包含搜索请求的dissertation plan
                reportorplan = updated_plan
                return reportorplan
            
            # 5. 执行coding agent（如果搜索判断后无需搜索）
            self.logger.info("workflow", "搜索判断完成，开始执行coding agent")
            reportorplan = await self._execute_coding_agent(updated_plan, is_first_time=False)
            return reportorplan
            
        except Exception as e:
            self.logger.error("workflow", f"生成报告时发生错误: {str(e)}")
            return ReportModel(
                 report=f"生成报告时发生错误: {str(e)}",
                 is_finish=False
             )
    
    async def _run_search_decision(self, dissertation_plan: DissertationPlan) -> DissertationPlan:
        """运行搜索决策模块
        
        Args:
            dissertation_plan: 输入的论文计划
            
        Returns:
            DissertationPlan: 更新后的论文计划（可能包含搜索请求）
        """
        # 创建临时文件保存输入计划
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_input:
            json.dump(dissertation_plan.model_dump(), temp_input, ensure_ascii=False, indent=2)
            temp_input_path = temp_input.name
        
        # 创建输出文件路径 - 保存到工作目录
        output_filename = "dissertation_plan_with_search_requests.json"
        output_path = os.path.join(self.working_dir, output_filename)
        
        try:
            # 运行搜索决策
            await run_decision(
                input_path=temp_input_path,
                output_path=output_path,
                working_dir=self.working_dir,
                background_paths=None  # 使用自动发现
            )
            
            # 读取结果
            if Path(output_path).exists():
                updated_plan = DissertationPlan.from_file(output_path)
                self.logger.info("search_decision", f"搜索需求文件已生成: {output_path}")
                return updated_plan
            else:
                self.logger.warning("search_decision", "搜索决策输出文件不存在，返回原计划")
                return dissertation_plan
                
        finally:
            # 只清理临时输入文件，保留工作目录中的输出文件
            if Path(temp_input_path).exists():
                Path(temp_input_path).unlink()
    
    async def _execute_coding_agent(self, dissertation_plan: DissertationPlan, is_first_time: bool = False) -> ReportModel:
        """执行coding agent
        
        Args:
            dissertation_plan: 论文计划
            is_first_time: 是否为第一次分析
            
        Returns:
            ReportModel: 生成的报告
        """
        try:
            # 直接传递DissertationPlan对象给run_intelligent_task
            result = await run_intelligent_task(
                dissertation_plan=dissertation_plan,
                working_dir=self.working_dir
            )
            
            # 从结果中提取ReportModel
            if result and isinstance(result, dict):
                # 检查是否包含agent_output字段（应该是ReportModel对象）
                if 'agent_output' in result:
                    agent_output = result['agent_output']
                    if hasattr(agent_output, 'report') and hasattr(agent_output, 'artifacts'):
                        # 直接使用agent_output作为ReportModel，设置is_finish=True
                        report = ReportModel(
                            report=agent_output.report,
                            artifacts=agent_output.artifacts,
                            is_finish=True
                        )
                    else:
                        # 如果agent_output不是ReportModel格式，创建新的
                        report_content = str(agent_output) if agent_output else "Agent执行完成"
                        report = ReportModel(
                            report=report_content,
                            is_finish=True
                        )
                else:
                    # 兜底处理：从其他字段提取内容
                    if 'final_message' in result:
                        report_content = result['final_message']
                    elif 'message' in result:
                        report_content = result['message']
                    else:
                        report_content = str(result)
                    
                    report = ReportModel(
                        report=report_content,
                        is_finish=True
                    )
            else:
                # 如果结果是字符串或其他格式
                report_content = str(result) if result else "Agent执行完成"
                report = ReportModel(
                    report=report_content,
                    is_finish=True
                )
            
            self.logger.info("coding_agent", f"Agent执行完成，生成报告长度: {len(report.report)}")
            return report
            
        except Exception as e:
            self.logger.error("coding_agent", f"执行coding agent时发生错误: {str(e)}")
            return ReportModel(
                report=f"执行coding agent时发生错误: {str(e)}",
                is_finish=False
            )

"""
        Workflow:
            1. 读取 dissertation_plan
            2. 检查是否为第一次分析
            3. 如果是第一次分析，直接输出原计划进入coding agent 使用raw analysis prompt 进行分析 返回report model（raw analysis）（分析代码仓库 产出分析md格式文件）
            4. 如果不是第一次分析，Search 模块判断是否要搜索,判断的标准是有没有实例化agent communication类。 如果没有实例化就要搜索，如果有实例化且实例化的agent communication中有response就不需要搜索
            5. 如果要搜索，分析需要搜索的内容， 返回dissertation_plan，但是实例化agent communicate类，填入id和request。
            6. 如果不需要搜索，dissertation plan直接输入进入coding agent，coding agent完成报告，ReportModelis_finish设置为 true
"""