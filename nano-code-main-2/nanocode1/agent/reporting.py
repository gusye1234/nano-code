from typing import List, Dict, Optional, Callable
from ..models.output_format import ReportModel
from .artifacts import ARTIFACT_TOOLS, get_artifact_file_identifier, merge_artifacts


async def build_agent_output(
    report: str,
    execution_log: List[dict],
    existing_report: Optional[ReportModel],
    is_first_time: bool = False,
    artifact_detector_func: Optional[Callable] = None
) -> ReportModel:
    """
    构建Agent输出，按照规定格式输出，选择最合适的附件类型
    
    如果有 existing_report，保持原有 report 内容不变，只合并 artifacts。
    对于第一次分析，将 architecture_analysis_report 内容合并到 report 中。
    
    Args:
        report: 报告内容
        execution_log: 执行日志
        existing_report: 现有报告（可选）
        is_first_time: 是否为第一次分析
        artifact_detector_func: artifact检测函数
        
    Returns:
        ReportModel: 输出结果
    """
    # 收集本次新生成的 artifacts
    new_artifacts = []
    processed_files = set()
    architecture_report_content = ""
    
    for log_entry in execution_log:
        tool_name = log_entry.get("tool", "")

        if tool_name in ARTIFACT_TOOLS:
            if artifact_detector_func:
                new_file_artifacts = await artifact_detector_func(log_entry)
            else:
                new_file_artifacts = []
            
            for artifact in new_file_artifacts:
                file_identifier = get_artifact_file_identifier(artifact)
                if file_identifier not in processed_files:
                    processed_files.add(file_identifier)
                    
                    # 第一次分析时，提取 architecture_analysis_report 内容并跳过该artifact
                    if (is_first_time and hasattr(artifact, 'title') and 
                        artifact.title.endswith('.md') and 
                        'architecture_analysis_report' in artifact.title):
                        # 读取文件内容
                        try:
                            if hasattr(artifact, 'file') and artifact.file:
                                with open(artifact.file, 'r', encoding='utf-8') as f:
                                    architecture_report_content = f.read()
                        except Exception:
                            pass
                        continue
                        
                    new_artifacts.append(artifact)
    
    # 简化合并逻辑
    if existing_report:
        # 保持原有 report，只合并 artifacts
        existing_artifacts = existing_report.artifacts or []
        combined_artifacts = merge_artifacts(existing_artifacts, new_artifacts)
        
        return ReportModel(
            report=existing_report.report,  # 保持不变
            artifacts=combined_artifacts
        )
    else:
        # 第一次：创建新报告，合并 architecture_analysis_report 内容
        final_report = report
        if architecture_report_content:
            final_report = f"{report}\n\n## 架构分析报告\n\n{architecture_report_content}"
            
        return ReportModel(
            report=final_report,
            artifacts=new_artifacts
        )


def extract_architecture_content(artifacts: List, is_first_time: bool) -> str:
    """
    从artifacts中提取architecture_analysis_report内容
    
    Args:
        artifacts: artifact列表
        is_first_time: 是否为第一次分析
        
    Returns:
        str: 架构报告内容
    """
    if not is_first_time:
        return ""
        
    for artifact in artifacts:
        if (hasattr(artifact, 'title') and 
            artifact.title.endswith('.md') and 
            'architecture_analysis_report' in artifact.title):
            try:
                if hasattr(artifact, 'file') and artifact.file:
                    with open(artifact.file, 'r', encoding='utf-8') as f:
                        return f.read()
            except Exception:
                pass
    return ""


def should_skip_architecture_artifact(artifact, is_first_time: bool) -> bool:
    """
    判断是否应该跳过architecture artifact
    
    Args:
        artifact: artifact对象
        is_first_time: 是否为第一次分析
        
    Returns:
        bool: 是否应该跳过
    """
    return (is_first_time and 
            hasattr(artifact, 'title') and 
            artifact.title.endswith('.md') and 
            'architecture_analysis_report' in artifact.title)


def create_final_report_with_architecture(report: str, architecture_content: str) -> str:
    """
    创建包含架构分析的最终报告
    
    Args:
        report: 原始报告内容
        architecture_content: 架构分析内容
        
    Returns:
        str: 合并后的报告内容
    """
    if architecture_content:
        return f"{report}\n\n## 架构分析报告\n\n{architecture_content}"
    return report


def create_incremental_report(existing_report: ReportModel, new_artifacts: List) -> ReportModel:
    """
    创建增量报告（保持原有报告，只合并artifacts）
    
    Args:
        existing_report: 现有报告
        new_artifacts: 新的artifacts
        
    Returns:
        ReportModel: 合并后的报告
    """
    existing_artifacts = existing_report.artifacts or []
    combined_artifacts = merge_artifacts(existing_artifacts, new_artifacts)
    
    return ReportModel(
        report=existing_report.report,  # 保持不变
        artifacts=combined_artifacts
    )


def create_new_report(report: str, artifacts: List, architecture_content: str = "") -> ReportModel:
    """
    创建全新报告
      
    Args:
        report: 报告内容
        artifacts: artifacts列表
        architecture_content: 架构分析内容（可选）
        
    Returns:
        ReportModel: 新报告
    """
    final_report = create_final_report_with_architecture(report, architecture_content)
    
    return ReportModel(
        report=final_report,
        artifacts=artifacts
    )


def collect_artifacts_from_log(
    execution_log: List[dict],
    artifact_detector_func: Optional[Callable] = None,
    is_first_time: bool = False
) -> tuple[List, str]:
    """
    从执行日志中收集artifacts
    
    Args:
        execution_log: 执行日志
        artifact_detector_func: artifact检测函数
        is_first_time: 是否为第一次分析
        
    Returns:
        tuple: (artifacts列表, architecture内容)
    """
    new_artifacts = []
    processed_files = set()
    architecture_report_content = ""
    
    for log_entry in execution_log:
        tool_name = log_entry.get("tool", "")

        if tool_name in ARTIFACT_TOOLS:
            if artifact_detector_func:
                new_file_artifacts = artifact_detector_func(log_entry)  # 假设是同步函数，如需异步需要调整
            else:
                new_file_artifacts = []
            
            for artifact in new_file_artifacts:
                file_identifier = get_artifact_file_identifier(artifact)
                if file_identifier not in processed_files:
                    processed_files.add(file_identifier)
                    
                    # 检查是否需要跳过architecture artifact
                    if should_skip_architecture_artifact(artifact, is_first_time):
                        # 提取架构报告内容
                        architecture_content = extract_architecture_content([artifact], is_first_time)
                        if architecture_content:
                            architecture_report_content = architecture_content
                        continue
                        
                    new_artifacts.append(artifact)
    
    return new_artifacts, architecture_report_content