import os
from ...constants import MAX_READ_FILE_LINES, MAX_LINE_CHAR_LENGTH
from ..base import AgentToolDefine, AgentToolReturn
from ...core.session import Session
from ...utils.file import is_text_file


class CreateFileTool(AgentToolDefine):
    @classmethod
    def init(cls, **kwargs):
        return cls(
            name="create_file",
            description="""Creates a new file in the local filesystem. You can use this tool to create a new file, including code, text, plans...""",
            parameters_schema={
                "properties": {
                    "file_path": {
                        "description": "The absolute path to the file to write to (e.g., '/home/user/project/file.txt'). Relative paths are not supported.",
                        "type": "string",
                    },
                    "content": {
                        "description": "The content to write to the file.",
                        "type": "string",
                    },
                },
                "required": ["file_path", "content"],
                "type": "object",
            },
        )

    async def _execute(self, session: Session, arguments) -> AgentToolReturn:
        absolute_path = arguments["file_path"]
        content = arguments["content"]

        absolute_path = os.path.abspath(absolute_path)

        if not session.path_within_root(absolute_path):
            return AgentToolReturn.error(
                self.name,
                f"File {absolute_path} is not within the working directory {session.working_dir}",
            )

        if os.path.exists(absolute_path):
            return AgentToolReturn.error(
                self.name,
                f"File {absolute_path} already exists, use edit_file tool to edit it",
            )

        dir_path = os.path.dirname(absolute_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        with open(absolute_path, "w") as f:
            f.write(content)
        return AgentToolReturn(
            for_llm=f"Write File {absolute_path} successfully",
            for_human=f"Write File {absolute_path} successfully",
        )
