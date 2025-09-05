from pydantic import BaseModel
from typing import List, Union, Any, Dict
import json
from pathlib import Path
from json_repair import repair_json

class ImageArtifact(BaseModel):
    """图像附件"""
    image: str  # Base64或文件路径
    title: str
    description: str
    @staticmethod
    def image_to_base64(image_path: str) -> str:
        """将图像文件转换为 Base64 字符串"""
        import base64
        with open(image_path, "rb") as image_file:
            # 读取图像文件的二进制数据
            image_data = image_file.read()
            # 转换为 Base64
            base64_string = base64.b64encode(image_data).decode('utf-8')
            return base64_string

class TableArtifact(BaseModel):
    """表格附件"""
    table: str  # CSV字符串或表格数据
    title: str
    description: str

class CodeArtifact(BaseModel):
    """代码附件"""
    code: str
    title: str
    description: str
 

class FileArtifact(BaseModel):
    """文件附件"""
    file: str  # 文件路径或内容
    title: str
    description: str

class ReportModel(BaseModel):
    """报告输出模型"""
    report: str  # 主报告内容
    artifacts: List[Union[ImageArtifact, TableArtifact, CodeArtifact, FileArtifact]] = []
    is_finish: bool = False
    
    def save_json(self, file_path: str):
        """保存为JSON文件"""
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, file_path: str):
        """从JSON文件加载"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)

    @classmethod
    def from_file(cls, file_path: str) -> 'ReportModel':
        """Load ReportModel from JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Report model file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            json_str = f.read()
        
        try:
            # 修复可能的JSON格式问题
            repaired_json = repair_json(json_str)
            # 解析为字典
            data = json.loads(repaired_json)
            # 转换为Pydantic模型对象
            return cls(**data)
        except Exception as e:
            raise ValueError(f"Failed to parse dissertation plan JSON: {e}")