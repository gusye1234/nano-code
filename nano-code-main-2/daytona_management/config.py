import os
import json
import time
from pathlib import Path
from typing import Tuple

class DaytonaConfig:
    """Daytona 沙盒配置管理"""
    
    def __init__(self, enable_volume: bool = False):
        self.api_key = self._load_daytona_api_key()
        self.api_url = "https://app.daytona.io/api"
        self.base_image = "python:3.11-slim"
        
    def _load_daytona_api_key(self) -> str:
        """从环境变量加载Daytona API密钥"""
        api_key = os.getenv('DAYTONA_API_KEY')
        if not api_key:
            api_key = "dtn_9a34a912ed7e52032cfea293549bb88762452ffd66550d45cdc503c9a7fcc0d8"
        return api_key


class LLMConfig:
    """LLM API配置管理"""
    
    def __init__(self):
        self.api_key, self.base_url = self._load_llm_config()
    
    def _load_llm_config(self) -> Tuple[str, str]:
        """获取LLM API配置"""
        # 优先从配置文件读取
        config_path = Path.home() / ".nano_code" / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                api_key = config.get('llm_api_key', '')
                base_url = config.get('llm_base_url', 'https://api.openai.com/v1')
                
                if api_key:
                    return api_key, base_url
            except Exception:
                pass
        
        # 从环境变量读取
        api_key = os.getenv('OPENAI_API_KEY', '')
        base_url = os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1')
        
        if not api_key:
            raise RuntimeError("未找到LLM API密钥配置")
        
        return api_key, base_url


class PathConfig:
    """路径配置常量"""
    
    WORKSPACE_ROOT = "/workspace"
    SYSTEM_DIR = "/workspace/system"
    DOWNLOAD_DIR = "/workspace/download"
    TMP_DIR = "/workspace/tmp"
    
    # 本地路径
    LOCAL_DOWNLOAD_DIR = Path.home() / "Desktop" / "SandboxWork" / "download"
    
    # 排除模式
    SKIP_PATTERNS = ['.pyc', '__pycache__', '.git', '.DS_Store', '.vscode']
    
    EXCLUDE_PATTERNS = [
        '.pyc', '__pycache__', 'venv', '.git', '.DS_Store',
        'pip-log.txt', 'pip-delete-this-directory.txt',
        '.gitignore', 'requirements.txt'
    ]