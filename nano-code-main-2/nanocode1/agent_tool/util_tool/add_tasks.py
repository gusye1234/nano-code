import re
from ..base import AgentToolDefine, AgentToolReturn
from ...core.session import Session

todos = []  # Global list to store parsed tasks

class AddTasksTool(AgentToolDefine):
    @classmethod
    def init(cls, **kwargs):
        return cls(
            name="add_tasks",
            description="""
            Adds todos to a global list by parsing markdown checkbox syntax.
            Accepts a string with lines such as '- [ ] Task description'.
            Ignores lines without valid task syntax.
            """,
            parameters_schema={
                "properties": {
                    "markdown": {
                        "description": "Markdown string with checkbox todos, e.g. '- [ ] Task1'.",
                        "type": "string",
                    }
                },
                "required": ["markdown"],
                "type": "object",
            },
        )

    async def _execute(self, session: Session, arguments) -> AgentToolReturn:
        global todos
        markdown = arguments["markdown"]
        # Regex for markdown checkbox tasks (only unchecked)
        pattern = r"^- \[ \] (.+)$"
        new_tasks = []
        for line in markdown.splitlines():
            match = re.match(pattern, line.strip())
            if match:
                task = match.group(1).strip()
                todos.append(task)
                new_tasks.append(task)
        return AgentToolReturn(
            for_llm=f"Added {len(new_tasks)} tasks.",
            for_human=f"Added {len(new_tasks)} tasks: {new_tasks}",
        )
