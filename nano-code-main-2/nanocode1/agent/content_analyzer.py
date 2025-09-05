from pathlib import Path
from ..core.session import Session
from ..llm import llm_complete
from ..prompts import (
    Graph_analysis_prompt, Data_anlaysis_prompt, 
    Code_analysis_prompt, File_analysis_prompt
)
from ..models.output_format import ImageArtifact


async def analyze_generated_content(session: Session, file_path: str, content: str = "", system_prompt: str = None) -> str:
    """
    分析生成的内容，根据文件类型选择不同prompt
    
    Args:
        session: 会话对象
        file_path: 文件路径
        content: 文件内容
        system_prompt: 系统提示词（如果为None，会使用默认的格式化系统提示词）
        
    Returns:
        str: 分析结果
    """
    file_extension = Path(file_path).suffix.lower()
    file_name = Path(file_path).name
    
    # 根据文件类型定制分析提示
    try:
        if file_extension in ['.png', '.jpg', '.jpeg', '.svg']:
            # 使用多模态Vision API格式
            try:
                base64code = ImageArtifact.image_to_base64(file_path)
                # 构建多模态消息
                text_prompt = Graph_analysis_prompt.format(file_name=file_name, file_path=file_path)
                
                # 根据文件扩展名设置正确的MIME类型
                mime_type = "image/png" if file_extension == '.png' else "image/jpeg"
                if file_extension == '.svg':
                    mime_type = "image/svg+xml"
                
                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64code}"}}
                    ]
                }]
            except Exception as e:
                # base64转换失败时使用文本分析
                messages = [{"role": "user", "content": f"分析图片文件失败: {file_name}，位置: {file_path}，错误: {str(e)}"}]

        elif file_extension in ['.csv', '.xlsx']:
            analysis_prompt = Data_anlaysis_prompt.format(file_name=file_name, file_path=file_path)
            messages = [{"role": "user", "content": analysis_prompt}]
        elif file_extension in ['.py']:
            analysis_prompt = Code_analysis_prompt.format(file_name=file_name, content=content)
            messages = [{"role": "user", "content": analysis_prompt}]
        else:
            analysis_prompt = File_analysis_prompt.format(file_name=file_name, content=content)
            messages = [{"role": "user", "content": analysis_prompt}]

        # 对于图片分析，使用专用的简洁系统提示词，不依赖执行上下文
        if file_extension in ['.png', '.jpg', '.jpeg', '.svg']:
            # 图片分析使用专门的系统提示词，确保纯粹的视觉分析
            system_prompt = "You are a professional image analysis expert. Analyze the provided image objectively and provide detailed insights about its visual content, structure, and meaning. Focus purely on what you observe in the image."
        elif system_prompt is None:
            # 对于其他文件类型，使用简单的默认系统提示词
            system_prompt = "You are an AI assistant analyzing generated files. Provide concise, helpful descriptions."

        analysis_response = await llm_complete(
            session,
            session.working_env.llm_main_model,
            messages,
            system_prompt=system_prompt
        )
        return analysis_response.choices[0].message.content
    except Exception as e:
        return f"分析生成时出错: {str(e)}"


def should_analyze_file(file_path: str) -> bool:
    """
    判断文件是否需要LLM分析
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否需要分析
    """
    file_extension = Path(file_path).suffix.lower()
    return file_extension in ['.png', '.jpg', '.jpeg', '.svg', '.csv', '.xlsx', '.py']


def get_file_analysis_type(file_path: str) -> str:
    """
    获取文件分析类型
    
    基于原文件的分析逻辑，返回文件的分析类别
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 分析类型 ('image', 'data', 'code', 'file')
    """
    file_extension = Path(file_path).suffix.lower()
    
    if file_extension in ['.png', '.jpg', '.jpeg', '.svg']:
        return 'image'
    elif file_extension in ['.csv', '.xlsx']:
        return 'data'
    elif file_extension in ['.py']:
        return 'code'
    else:
        return 'file'


def needs_content_for_analysis(file_path: str) -> bool:
    """
    判断分析时是否需要文件内容

    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否需要读取文件内容
    """
    file_extension = Path(file_path).suffix.lower()
    # 只有Python文件需要读取内容进行分析
    return file_extension == '.py'