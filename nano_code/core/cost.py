from dataclasses import dataclass
from openai.types.chat import ChatCompletion


@dataclass
class LLMCheckpoint:
    messages: list
    response: ChatCompletion
    finish_response_time: float = 0

    def to_json(self):
        return {
            "messages": self.messages,
            "response": self.response.model_dump(),
            "finish_response_time": self.finish_response_time,
        }


@dataclass
class LLMCheckpointFailed:
    messages: list
    error: Exception

    def to_json(self):
        return {
            "messages": self.messages,
            "error": str(self.error),
        }


@dataclass
class ToolCheckpoint:
    tool_name: str
    tool_args: dict
    tool_results: dict
    tool_finish_time: float = 0

    def to_json(self):
        return {
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "tool_results": self.tool_results,
            "tool_finish_time": self.tool_finish_time,
        }


@dataclass
class ToolCheckpointFailed:
    tool_name: str
    tool_args: dict
    error: Exception

    def to_json(self):
        return {
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "error": str(self.error),
        }
