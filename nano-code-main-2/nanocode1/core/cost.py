from dataclasses import dataclass
from openai.types.chat import ChatCompletion


@dataclass
class LLMUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    def to_json(self):
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class LLMCheckpoint:
    messages: list
    response: dict
    finish_response_time: float = 0
    usage: LLMUsage = None

    def to_json(self):
        return {
            "messages": self.messages,
            "response": self.response,
            "finish_response_time": self.finish_response_time,
            "usage": self.usage.to_json(),
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
