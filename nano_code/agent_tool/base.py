import asyncio
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any
from enum import StrEnum
from ..core.session import Session
from ..core.cost import ToolCheckpointFailed, ToolCheckpoint
from ..agent_tool.tool_schema import SchemaValidator
from ..constants import MAX_FOR_LLM_TOOL_RETURN_TOKENS
from ..utils.tokens import truncate_text


class ToolBehavior(StrEnum):
    READONLY = "readonly"
    MODIFY = "modify"


class AgentToolReturn(BaseModel):
    for_llm: str
    for_human: str

    @classmethod
    def error(cls, name: str, message: str) -> "AgentToolReturn":
        return cls(
            for_llm=f"Error on executing `{name}` tool: {message}", for_human=message
        )


class AgentToolDefine(BaseModel, ABC):
    name: str
    description: str
    parameters_schema: dict[str, Any]

    behavior: ToolBehavior = ToolBehavior.READONLY

    def get_function_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
            "strict": True,
        }

    @classmethod
    @abstractmethod
    def init(cls, **kwargs) -> "AgentToolDefine":
        raise NotImplementedError("Function must implement init method")

    def validate_arguments(self, arguments) -> AgentToolReturn | None:
        ok, err = SchemaValidator.validate(self.parameters_schema, arguments)
        if not ok:
            return AgentToolReturn(
                for_llm=f"Error: Invalid parameters provided to {self.name}. Reason: {err}",
                for_human=err,
            )
        return None

    @abstractmethod
    async def _execute(self, session: Session, arguments: dict) -> AgentToolReturn:
        raise NotImplementedError("Function must implement _execute method")

    async def execute(self, session: Session, arguments: dict) -> AgentToolReturn:
        try:
            v = self.validate_arguments(arguments)
            if v is not None:
                return v

            start_time = asyncio.get_event_loop().time()
            r = await self._execute(session, arguments)
            finish_time = asyncio.get_event_loop().time()

            r.for_llm = truncate_text(r.for_llm, MAX_FOR_LLM_TOOL_RETURN_TOKENS)
            session.update_tool_checkpoint(
                ToolCheckpoint(
                    tool_name=self.name,
                    tool_args=arguments,
                    tool_results=r.model_dump(),
                    tool_finish_time=finish_time - start_time,
                )
            )
            return r
        except Exception as e:
            session.update_tool_checkpoint(
                ToolCheckpointFailed(
                    tool_name=self.name,
                    tool_args=arguments,
                    error=e,
                )
            )
            return AgentToolReturn.error(self.name, str(e))

    def get_execution_description(self, arguments: dict) -> str:
        return f"Executing {self.name} with arguments: {arguments}"
