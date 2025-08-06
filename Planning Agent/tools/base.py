"""
基础工具类定义
参考nanocode的AgentToolDefine设计
"""

import asyncio
import json
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any, Dict
from enum import StrEnum


class ToolBehavior(StrEnum):
    READONLY = "readonly"
    MODIFY = "modify"


class AgentToolReturn(BaseModel):
    """工具执行返回结果"""
    for_llm: str      # 给LLM看的结果
    for_human: str    # 给用户看的结果

    @classmethod
    def error(cls, name: str, message: str) -> "AgentToolReturn":
        return cls(
            for_llm=f"Error on executing `{name}` tool: {message}", 
            for_human=message
        )

    @classmethod
    def success(cls, name: str, result: Dict[str, Any]) -> "AgentToolReturn":
        result_json = json.dumps(result, indent=2, ensure_ascii=False)
        return cls(
            for_llm=f"Successfully executed `{name}` tool. Result:\n{result_json}",
            for_human=f"Tool {name} executed successfully"
        )


class AgentToolDefine(BaseModel, ABC):
    """工具定义基类"""
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    behavior: ToolBehavior = ToolBehavior.READONLY

    def get_function_schema(self) -> Dict[str, Any]:
        """获取OpenAI function calling格式的schema"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }

    @classmethod
    @abstractmethod
    def init(cls, **kwargs) -> "AgentToolDefine":
        """初始化工具实例"""
        raise NotImplementedError("Tool must implement init method")

    def validate_arguments(self, arguments: Dict[str, Any]) -> AgentToolReturn | None:
        """验证输入参数"""
        # 简化版验证，检查必需参数
        required_props = self.parameters_schema.get("required", [])
        for prop in required_props:
            if prop not in arguments:
                return AgentToolReturn.error(
                    self.name, 
                    f"Missing required parameter: {prop}"
                )
        return None

    @abstractmethod
    async def _execute(self, arguments: Dict[str, Any]) -> AgentToolReturn:
        """执行工具的核心逻辑"""
        raise NotImplementedError("Tool must implement _execute method")

    async def execute(self, arguments: Dict[str, Any]) -> AgentToolReturn:
        """执行工具（带验证和错误处理）"""
        try:
            # 验证参数
            validation_error = self.validate_arguments(arguments)
            if validation_error is not None:
                return validation_error

            # 执行核心逻辑
            result = await self._execute(arguments)
            return result

        except Exception as e:
            return AgentToolReturn.error(self.name, str(e))

    def get_execution_description(self, arguments: Dict[str, Any]) -> str:
        """获取执行描述"""
        return f"Executing {self.name} with arguments: {arguments}"


class ToolRegistry:
    """工具注册系统"""
    
    def __init__(self):
        self.__tools: Dict[str, AgentToolDefine] = {}

    def register(self, tool: AgentToolDefine):
        """注册工具"""
        self.__tools[tool.name] = tool
        print(f"🔧 Tool registered: {tool.name}")

    def add_tools(self, tools: list[AgentToolDefine]):
        """批量注册工具"""
        for tool in tools:
            self.register(tool)

    def get_all_tools(self) -> list[AgentToolDefine]:
        """获取所有工具"""
        return list(self.__tools.values())

    def get_schemas(self) -> list[Dict[str, Any]]:
        """获取所有工具的function schemas"""
        return [tool.get_function_schema() for tool in self.__tools.values()]

    def list_tools(self) -> list[str]:
        """列出所有工具名称"""
        return list(self.__tools.keys())

    def has_tool(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self.__tools

    def merge(self, other: "ToolRegistry") -> "ToolRegistry":
        """合并另一个工具注册表"""
        self.add_tools(other.get_all_tools())
        return self

    async def execute(self, name: str, arguments: Dict[str, Any]) -> AgentToolReturn:
        """执行指定工具"""
        if not self.has_tool(name):
            return AgentToolReturn.error(name, f"Tool '{name}' not found")
        
        tool = self.__tools[name]
        result = await tool.execute(arguments)
        print(f"🍺 {name}: {result.for_human}")
        return result