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
        
    async def generate_report(self, dissertation_plan: DissertationPlan, report_model: Optional[ReportModel] = None) -> ReportOrPlan:
        """
        生成报告的方法，完整的workflow
        
        Args:
            dissertation_plan: 论文计划
            report_model: 可选的报告模型，指定输出格式
            
        Returns:
            ReportOrPlan: 根据情况返回ReportModel或DissertationPlan
                - 如果需要搜索: 返回包含agent_communicate的DissertationPlan
                - 如果完成分析: 返回ReportModel
        """
        try:
            # 1. 检查是否为第一次分析
            if dissertation_plan.is_first_time:
                report = await self._execute_coding_agent(dissertation_plan, report_model=report_model)   
                return report
            
            # 2. 检查literature_topic是否为空列表，如果为空则直接跳过搜索判断
            if not dissertation_plan.literature_topic:
                report = await self._execute_coding_agent(dissertation_plan, report_model=report_model)
                return report
            
            # 3. 检查是否已有完整的搜索响应
            if (hasattr(dissertation_plan, 'agent_communicate') and 
                dissertation_plan.agent_communicate and 
                all(comm.response != "" for comm in dissertation_plan.agent_communicate)):
                report = await self._execute_coding_agent(dissertation_plan, report_model=report_model)
                return report
            
            # 4. 非第一次分析且无完整搜索响应，进行搜索判断
            updated_plan = await self._run_search_decision(dissertation_plan)
            
            # 5. 检查搜索判断结果
            if updated_plan.agent_communicate and any(comm.response == "" for comm in updated_plan.agent_communicate):
                # 返回包含搜索请求的dissertation plan
                return updated_plan
            
            # 6. 执行coding agent（如果搜索判断后无需搜索）
            report = await self._execute_coding_agent(updated_plan, report_model=report_model)
            return report
            
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
            )
            
            # 读取结果
            if Path(output_path).exists():
                updated_plan = DissertationPlan.from_file(output_path)
                return updated_plan
            else:
                return dissertation_plan
                
        finally:
            # 只清理临时输入文件，保留工作目录中的输出文件
            if Path(temp_input_path).exists():
                Path(temp_input_path).unlink()
    
    async def _execute_coding_agent(self, dissertation_plan: DissertationPlan,  report_model: Optional[ReportModel] = None) -> ReportModel:
        """执行coding agent
        
        Args:
            dissertation_plan: 论文计划
            is_first_time: 是否为第一次分析
            report_model: 可选的报告模型，指定输出格式
            
        Returns:
            ReportModel: 生成的报告
        """
        try:
            # 传递DissertationPlan对象和existing_report给run_intelligent_task
            result = await run_intelligent_task(
                dissertation_plan=dissertation_plan,
                working_dir=self.working_dir,
                existing_report=report_model
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
            1. 读取 dissertation_plan和report model（如果有）
            2. 检查是否为第一次分析
            3. 如果是第一次分析，直接输出原计划进入coding agent 使用raw analysis prompt 进行分析 返回report model（raw analysis）（分析代码仓库 产出分析md格式文件）
            4. 如果不是第一次分析，即同时输入dissertation plan和report model（此时只包含markdown文本，mmd文件和png文件）
            4.1 Search 模块判断是否要搜索,判断的标准是有没有实例化agent communication类。 如果没有实例化就要搜索，如果有实例化且实例化的agent communicate中有response就不需要搜索
            5. 如果要搜索，分析需要搜索的内容， 返回dissertation_plan，但是实例化agent communicate类，填入id和request。
            6. 如果不需要搜索，dissertation plan直接输入进入coding agent，coding agent完成报告，ReportModelis_finish设置为 true
"""