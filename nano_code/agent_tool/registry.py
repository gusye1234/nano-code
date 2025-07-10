from .base import AgentToolDefine, AgentToolReturn
from ..core.session import Session


class ToolRegistry:
    def __init__(self):
        self.__tools: dict[str, AgentToolDefine] = {}

    def register(self, tool: AgentToolDefine):
        self.__tools[tool.name] = tool

    def add_tools(self, tools: list[AgentToolDefine]):
        for tool in tools:
            self.register(tool)

    def get_all_tools(self):
        return list(self.__tools.values())

    def get_schemas(self):
        return [tool.get_function_schema() for tool in self.__tools.values()]

    def list_tools(self):
        return list(self.__tools.keys())

    def has_tool(self, name: str):
        return name in self.__tools

    def merge(self, other: "ToolRegistry"):
        self.add_tools(other.get_all_tools())
        return self

    async def execute(
        self, session: Session, name: str, arguments: dict
    ) -> AgentToolReturn:
        r = await self.__tools[name].execute(session, arguments)
        session.log(f"🍺 {name}: {r.for_human}")
        return r
