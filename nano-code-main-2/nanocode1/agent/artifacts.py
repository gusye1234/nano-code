import os
import time
from typing import List, Callable, Optional
from pathlib import Path
from ..core.session import Session
from ..models.output_format import ImageArtifact, TableArtifact, CodeArtifact, FileArtifact
from .content_analyzer import should_analyze_file, needs_content_for_analysis


ARTIFACT_TOOLS = ["create_file", "write_file", "RunCommand", "render_mermaid"]


async def detect_new_artifacts(
    log_entry: dict, 
    session: Session, 
    analyzer_func: Optional[Callable] = None
) -> List:
    """
    检测工具执行后新创建的文件并创建对应artifacts
    
    Args:
        log_entry: 工具执行日志
        session: 会话对象
        analyzer_func: 内容分析函数（可选）
        
    Returns:
        list: 新创建的artifact列表
    """
    artifacts = []
    
    # 从日志中获取执行前后的文件时间戳信息
    file_changes = log_entry.get("file_changes", {})
    new_files = file_changes.get("created", [])
    
    # 如果没有文件变化信息，回退到扫描工作目录（但只扫描一次）
    if not new_files:
        # 检查是否已经扫描过最近文件
        if not getattr(session, '_recent_files_scanned', False):
            new_files = scan_recent_files(session.working_dir, session)
            session._recent_files_scanned = True
        else:
            new_files = []
    
    for file_path in new_files:
        if not Path(file_path).exists():
            continue
            
        # 为每个文件单独获取或生成LLM分析结果
        file_specific_analysis = log_entry.get("llm_analysis", "")
        
        # 如果没有现有分析，为需要分析的文件类型生成分析
        if not file_specific_analysis and analyzer_func:
            if should_analyze_file(file_path):
                try:
                    # 读取文件内容用于分析
                    content = ""
                    if needs_content_for_analysis(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    file_specific_analysis = await analyzer_func(file_path, content)
                except Exception as e:
                    file_specific_analysis = f"无法分析文件: {str(e)}"
        
        artifact = create_artifact_by_extension(file_path, file_specific_analysis)
        if artifact:
            artifacts.append(artifact)
    
    return artifacts


def scan_recent_files(working_dir: str, session: Session) -> List[str]:
    """
    扫描工作目录中最近创建的有意义文件（仅根目录，不递归子文件夹）
    
    Args:
        working_dir: 工作目录路径
        session: 会话对象（用于ignore_path检查）
        
    Returns:
        list: 最近创建的文件路径列表
    """
    current_time = time.time()
    recent_files = set()  # 去重
    
    # 只关注核心文件格式
    target_extensions = {'.csv', '.py', '.png', '.jpg', '.jpeg', '.svg', '.md', '.xlsx', '.txt'}
    
    # 需要跳过的文件/目录模式
    skip_patterns = {'__pycache__', '.pytest_cache', '.git', '.cache', 'node_modules', '.venv', 'venv'}
    
    try:
        # 只扫描根目录，不使用os.walk递归
        files = os.listdir(working_dir)
        
        for file in files:
            # 跳过缓存目录和文件
            if any(pattern in file.lower() for pattern in skip_patterns):
                continue
                
            file_path = os.path.join(working_dir, file)
            
            # 跳过目录
            if os.path.isdir(file_path):
                continue
            
            # 只处理目标扩展名的文件
            if not any(file.lower().endswith(ext) for ext in target_extensions):
                continue
                
            if not session.ignore_path(file_path):
                # 检查文件是否在最近5分钟内创建
                if current_time - os.path.getctime(file_path) < 300:
                    recent_files.add(file_path)
    except Exception:
        pass
        
    return list(recent_files)


def create_artifact_by_extension(file_path: str, analysis: str = ""):
    """
    根据文件扩展名创建对应的artifact
    
    提取自原文件第358-401行的artifact创建逻辑
    
    Args:
        file_path: 文件路径
        analysis: LLM分析结果
        
    Returns:
        Artifact对象或None
    """
    try:
        file_extension = Path(file_path).suffix.lower()
        file_name = Path(file_path).name
        
        if file_extension in ['.png', '.jpg', '.jpeg', '.svg']:
            return ImageArtifact(
                image=file_path,
                title=file_name,
                description=analysis  # 完全依赖LLM分析
            )
        
        elif file_extension in ['.csv', '.xlsx']:
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
        
        elif file_extension in ['.md', '.txt']:
            # 为文档文件提供基本描述
            if not analysis:
                if file_extension == '.md':
                    analysis = f"Markdown文档: {file_name}"
                else:
                    analysis = f"文本文档: {file_name}"
            return FileArtifact(
                file=file_path,
                title=file_name,
                description=analysis
            )
            
    except Exception:
        return None


def get_artifact_file_identifier(artifact) -> str:
    """
    获取artifact的唯一标识符用于去重
    
    提取自原文件第252-254行的标识符获取逻辑
    
    Args:
        artifact: Artifact对象
        
    Returns:
        str: 唯一标识符
    """
    return getattr(artifact, 'title', '')


def merge_artifacts(existing_artifacts: List, new_artifacts: List) -> List:
    """
    简化的artifacts合并：保持现有的，添加新的（去重）
    
    提取自原文件第256-274行的artifact合并逻辑
    
    Args:
        existing_artifacts: 现有artifact列表
        new_artifacts: 新artifact列表
        
    Returns:
        list: 合并后的artifact列表
    """
    if not existing_artifacts:
        return new_artifacts or []
    
    if not new_artifacts:
        return existing_artifacts
    
    # 简单去重：基于 title 避免重复文件
    existing_titles = {get_artifact_file_identifier(artifact) for artifact in existing_artifacts}
    merged = existing_artifacts.copy()
    
    for artifact in new_artifacts:
        title = get_artifact_file_identifier(artifact)
        if title and title not in existing_titles:
            merged.append(artifact)
            existing_titles.add(title)
    
    return merged


def is_artifact_tool(tool_name: str) -> bool:
    """
    判断工具是否会产生artifact
    
    基于原文件第208行和第670行的工具判断逻辑
    
    Args:
        tool_name: 工具名称
        
    Returns:
        bool: 是否为artifact工具
    """
    return tool_name in ARTIFACT_TOOLS


def should_analyze_for_tool(tool_name: str, file_extension: str) -> bool:
    """
    判断特定工具和文件类型是否需要深度分析
    
    基于原文件第676-682行的分析判断逻辑
    
    Args:
        tool_name: 工具名称
        file_extension: 文件扩展名
        
    Returns:
        bool: 是否需要深度分析
    """
    if not is_artifact_tool(tool_name):
        return False
        
    # 只为需要深度分析的文件类型生成LLM分析
    return file_extension.lower() in ['.py', '.csv', '.xlsx', '.png', '.jpg', '.jpeg', '.svg']