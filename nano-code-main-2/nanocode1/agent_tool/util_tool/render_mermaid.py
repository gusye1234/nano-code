import asyncio
import base64
import logging
import zlib
import requests
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from ..base import AgentToolDefine, AgentToolReturn, ToolBehavior
from ...core.session import Session

logger = logging.getLogger(__name__)


@dataclass
class RenderConfig:
    """渲染配置参数组合"""
    width: int = 1200
    scale: float = 3.0
    bg_color: str = "white"
    max_retries: int = 3
    
    @property
    def actual_width(self) -> int:
        """计算实际渲染宽度"""
        return int(self.width * self.scale)


class MermaidSyntaxValidator:
    """Mermaid语法验证器"""
    
    @staticmethod 
    def is_syntax_error(error_message: str) -> bool:
        """判断是否为语法错误"""
        syntax_indicators = ['syntax error', 'parse error', '语法错误']
        return any(indicator in error_message.lower() for indicator in syntax_indicators)
    
    @staticmethod  
    def is_valid_png(response_data: bytes) -> bool:
        """验证响应是否为有效PNG文件（放宽：仅检查PNG头）"""
        return response_data.startswith(b'\x89PNG')


class MermaidRenderTool(AgentToolDefine):
    """渲染Mermaid图表为PNG图片"""
    
    name: str = "render_mermaid"
    description: str = """渲染Mermaid图表文件为高清PNG图片。
    用法: 提供.mmd文件的绝对路径，工具将使用mermaid.ink在线API渲染为PNG图片并保存到同一目录。
    支持分辨率控制：scale参数控制清晰度倍数，默认3x倍高分辨率渲染。
    注意: 输入路径必须是绝对路径，且文件必须存在。"""
    
    parameters_schema: dict = {
        "type": "object", 
        "properties": {
            "mermaid_file_path": {
                "type": "string",
                "description": "Mermaid文件的绝对路径（.mmd文件）"
            },
            "output_width": {
                "type": "integer", 
                "description": "输出图片的宽度（像素，默认1200）",
                "default": 1200
            },
            "scale": {
                "type": "number",
                "description": "渲染分辨率倍数（1-4，默认3，数值越高清晰度越高）",
                "default": 3,
                "minimum": 1,
                "maximum": 4
            },
            "bg_color": {
                "type": "string",
                "description": "背景颜色（默认white）",
                "default": "white"
            }
        },
        "required": ["mermaid_file_path"]
    }
    
    behavior: ToolBehavior = ToolBehavior.MODIFY  # 因为会创建PNG文件
    
    @classmethod
    def init(cls, **kwargs) -> "MermaidRenderTool":
        return cls()
    
    async def _execute(self, session: Session, arguments: dict) -> AgentToolReturn:
        """执行Mermaid渲染"""
        try:
            # 构建配置和验证输入
            config = RenderConfig(
                width=arguments.get("output_width", 1200),
                scale=arguments.get("scale", 3),
                bg_color=arguments.get("bg_color", "white")
            )
            
            mermaid_path, content = self._validate_and_read_file(arguments["mermaid_file_path"])
            
            # 渲染图表
            png_path = await self._render_diagram(mermaid_path, content, config)
            
            return self._create_success_response(mermaid_path, png_path, config)
            
        except Exception as e:
            return self._handle_error(e, arguments.get("mermaid_file_path", "unknown"))
    
    def _validate_and_read_file(self, file_path: str) -> Tuple[Path, str]:
        """验证文件并读取内容"""
        if not Path(file_path).is_absolute():
            raise ValueError(f"路径必须是绝对路径: {file_path}")
        
        mermaid_path = Path(file_path)
        
        if not mermaid_path.exists():
            raise FileNotFoundError(f"Mermaid文件不存在: {file_path}")
        
        if mermaid_path.suffix.lower() != '.mmd':
            raise ValueError(f"文件必须是.mmd扩展名: {file_path}")
        
        with open(mermaid_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        if not content:
            raise ValueError(f"Mermaid文件内容为空: {file_path}")
            
        return mermaid_path, content
    
    async def _render_diagram(self, mermaid_path: Path, content: str, config: RenderConfig) -> Path:
        """渲染图表主逻辑"""
        logger.info(f"开始渲染Mermaid图表: {mermaid_path.name}")
        
        try:
            return await self._render_with_api(content, mermaid_path, config)
        except Exception as e:
            if MermaidSyntaxValidator.is_syntax_error(str(e)):
                raise Exception(f"MERMAID_SYNTAX_ERROR: {str(e)}")
            raise
    
    def _create_success_response(self, mermaid_path: Path, png_path: Path, config: RenderConfig) -> AgentToolReturn:
        """创建成功响应"""
        return AgentToolReturn(
            for_llm=f"成功渲染Mermaid图表: {mermaid_path.name} -> {png_path.name}",
            for_human=f"✅ Mermaid图表渲染完成\n"
                     f"📊 输入: {mermaid_path.name}\n"
                     f"🖼️  输出: {png_path}\n"
                     f"📏 尺寸: {config.width}px宽\n"
                     f"🔍 分辨率: {config.scale}x倍\n"
                     f"🎨 背景: {config.bg_color}"
        )
    
    def _handle_error(self, error: Exception, file_path: str) -> AgentToolReturn:
        """统一错误处理"""
        error_msg = str(error)
        
        if "MERMAID_SYNTAX_ERROR" in error_msg:
            return AgentToolReturn(
                for_llm=f"MERMAID_SYNTAX_ERROR: 渲染失败，请检查并修复{Path(file_path).name}中的Mermaid语法错误。"
                       f"错误信息: {error_msg}。"
                       f"请重新检查Mermaid代码语法，修复错误后使用edit_file工具更新文件，然后重新调用render_mermaid。"
                       ,
                for_human=f"⚠️  Mermaid渲染失败，正在自动调试语法..."
            )
        
        logger.error(f"Mermaid渲染失败: {error}")
        return AgentToolReturn.error(self.name, f"渲染失败: {error_msg}")
    
    async def _render_with_api(self, content: str, mermaid_path: Path, config: RenderConfig) -> Path:
        """使用mermaid.ink API渲染图表"""
        png_path = mermaid_path.with_suffix('.png')

        for attempt in range(config.max_retries):
            try:
                # 自适应降级：先降scale，再降width
                current_scale = max(1, int(config.scale) - attempt)
                # 当scale已降到1后，再逐步降低基准宽度
                width_factor = 1.0
                over = attempt - max(0, int(config.scale) - 1)
                if over > 0:
                    # 第一次超出：0.75，之后：0.5（保持简单、可预期）
                    width_factor = 0.75 if over == 1 else 0.5

                attempt_width = max(300, int(config.width * current_scale * width_factor))

                urls = self._build_api_urls(content, attempt_width, config.bg_color)
                logger.info(
                    f"调用mermaid.ink API (尝试 {attempt + 1}/{config.max_retries}) "
                    f"width={attempt_width}, scale={current_scale}, urls={len(urls)}"
                )

                last_error: Exception | None = None
                for url in urls:
                    try:
                        response_data = await self._make_http_request(url)
                        self._validate_response(response_data)
                        # 保存PNG文件
                        png_path.write_bytes(response_data)
                        logger.info(f"PNG文件保存成功: {png_path}")
                        return png_path
                    except Exception as inner:
                        last_error = inner
                        logger.debug(f"URL 失败，尝试下一个编码方式: {inner}")

                # 所有URL编码方式都失败，抛出最后的错误
                if last_error:
                    raise last_error
                
            except Exception as e:
                if self._should_retry(e, attempt, config.max_retries):
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                    continue
                raise
        
        raise Exception(f"经过 {config.max_retries} 次尝试后渲染失败")

    def _build_api_urls(self, content: str, width: int, bg_color: str) -> list[str]:
        """构建API URL（优先使用pako压缩，回退到普通base64）"""
        urls: list[str] = []

        # 1) pako 压缩（raw DEFLATE）
        try:
            compressor = zlib.compressobj(level=9, wbits=-15)
            deflated = compressor.compress(content.encode("utf-8")) + compressor.flush()
        except Exception:
            deflated = b""

        if deflated:
            b64 = base64.urlsafe_b64encode(deflated).decode("ascii")
            urls.append(f"https://mermaid.ink/img/pako:{b64}?type=png&width={width}&bgColor={bg_color}")

        # 2) 普通 base64（非压缩）
        encoded_content = base64.urlsafe_b64encode(content.encode('utf8')).decode('ascii')
        urls.append(f"https://mermaid.ink/img/{encoded_content}?type=png&width={width}&bgColor={bg_color}")

        return urls
    
    async def _make_http_request(self, url: str) -> bytes:
        """执行HTTP请求"""
        def make_request():
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, make_request)
    
    def _validate_response(self, response_data: bytes) -> None:
        """验证API响应"""
        if not MermaidSyntaxValidator.is_valid_png(response_data):
            error_text = response_data.decode('utf-8', errors='ignore')[:200]
            if MermaidSyntaxValidator.is_syntax_error(error_text):
                raise Exception(f"Mermaid语法错误，服务器返回: {error_text}")
            else:
                raise Exception(f"API返回错误响应 ({len(response_data)} bytes): {error_text}")
    
    def _should_retry(self, error: Exception, attempt: int, max_retries: int) -> bool:
        """判断是否应该重试"""
        if MermaidSyntaxValidator.is_syntax_error(str(error)):
            return False  # 语法错误不重试
        return attempt < max_retries - 1 