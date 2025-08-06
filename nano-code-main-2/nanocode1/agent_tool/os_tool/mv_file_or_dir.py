import os
from ..base import AgentToolDefine, AgentToolReturn
from ...core.session import Session


class MoveFileOrDirTool(AgentToolDefine):
    @classmethod
    def init(cls, **kwargs):
        return cls(
            name="mv_file_or_dir",
            description="""Moves (renames) a file or directory to a new location, like Unix 'mv' or Python os.rename/shutil.move. Accepts absolute paths only.""",
            parameters_schema={
                "properties": {
                    "from_path": {
                        "description": "The absolute path of the file or directory to move. Must be inside the workspace.",
                        "type": "string",
                        "pattern": "^/",
                    },
                    "to_path": {
                        "description": "The destination absolute path where to move the file or directory. Must be inside the workspace and must not exist.",
                        "type": "string",
                        "pattern": "^/",
                    },
                },
                "required": ["from_path", "to_path"],
                "type": "object",
            },
        )

    async def _execute(self, session: Session, arguments) -> AgentToolReturn:
        from_path = os.path.abspath(arguments["from_path"])
        to_path = os.path.abspath(arguments["to_path"])

        if not session.path_within_root(from_path):
            return AgentToolReturn.error(
                self.name,
                f"Source path {from_path} is not within the working directory {session.working_dir}",
            )
        if not session.path_within_root(to_path):
            return AgentToolReturn.error(
                self.name,
                f"Destination path {to_path} is not within the working directory {session.working_dir}",
            )
        if not os.path.exists(from_path):
            return AgentToolReturn.error(
                self.name,
                f"Source path {from_path} does not exist",
            )
        if os.path.exists(to_path):
            return AgentToolReturn.error(
                self.name,
                f"Destination path {to_path} already exists!",
            )
        try:
            os.rename(from_path, to_path)
        except Exception as e:
            return AgentToolReturn.error(
                self.name,
                f"Failed to move: {e}",
            )
        return AgentToolReturn(
            for_llm=f"Moved {from_path} to {to_path} successfully",
            for_human=f"Moved {from_path} to {to_path} successfully",
        )
