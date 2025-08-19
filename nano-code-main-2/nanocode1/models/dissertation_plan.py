"""
Dissertation plan models for nanocode1.

This module defines the data models for dissertation research plans.
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from json_repair import repair_json


class CodeRepositoryReview(BaseModel):
    url: str
    description: str
    analysis_focus: List[str]


class ReproductionTask(BaseModel):
    phase: str
    target: str
    methodology: str


class CriticalEvaluation(BaseModel):
    failure_case_study: str
    improvement_directions: List[str]


class ExperimentalRequirements(BaseModel):
    code_repository_review: CodeRepositoryReview
    reproduction_tasks: List[ReproductionTask]
    critical_evaluation: CriticalEvaluation


class UrlInfo(BaseModel):
    url: str
    description: str


class DissertationPlan(BaseModel):
    dissertation_title: str
    literature_topic: List[str]
    experimental_requirements: ExperimentalRequirements
    urls: List[UrlInfo]
    
    @classmethod
    def from_file(cls, file_path: str) -> 'DissertationPlan':
        """Load DissertationPlan from JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dissertation plan file not found: {file_path}")
        
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