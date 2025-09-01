from pydantic import BaseModel
from typing import List, Union, Any, Dict
import json
from pathlib import Path

class ImageArtifact(BaseModel):
    """图像附件"""
    image: str  # Base64或文件路径
    title: str
    description: str
    def image_to_base64(self, image_path):
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