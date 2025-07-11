import os
from ...constants import MAX_READ_FILE_LINES, MAX_LINE_CHAR_LENGTH
from ..base import AgentToolDefine, AgentToolReturn
from ...core.session import Session
from ...utils.file import is_text_file


class EditFileTool(AgentToolDefine):
    @classmethod
    def init(cls, **kwargs):
        return cls(
            name="edit_file",
            description="""Edit content of a specified file in the local filesystem. 
You can use this tool to edit an existing file. By using different combinations of the parameters, you can edit different parts of the file.
When edit file, always make sure you read the current content of the file first.

For example:
- Replace first 10 lines with content `hello world`:
{
    "file_path": "/home/user/project/file.txt",
    "content": "hello\nworld",
    "start_line": 1,
    "end_line": 10
}
- Insert `hello world` before the 10th line:
{
    "file_path": "/home/user/project/file.txt",
    "content": "hello\nworld",
    "start_line": 10,
}
- If file's line number is 10, then insert a content at the end is:
{
    "file_path": "/home/user/project/file.txt",
    "content": "hello\nworld",
    "start_line": 11,
}
- Delete the first 10 lines:
{
    "file_path": "/home/user/project/file.txt",
    "content": "",
    "start_line": 1,
    "end_line": 10
}
""",
            parameters_schema={
                "properties": {
                    "file_path": {
                        "description": "The absolute path to the file to write to (e.g., '/home/user/project/file.txt'). Relative paths are not supported.",
                        "type": "string",
                    },
                    "content": {
                        "description": "The content to write to the file. If you want to delete, set it to an empty string. Multiple lines should be separated by newlines.",
                        "type": "string",
                    },
                    "start_line": {
                        "description": "The start line of the file to edit. minimum value is 1",
                        "type": "number",
                    },
                    "end_line": {
                        "description": "The end line of the file to edit. if null, meaning you're inserting content before the start line",
                        "type": "number",
                    },
                },
                "required": ["file_path", "content", "start_line"],
                "type": "object",
            },
        )

    async def _execute(self, session: Session, arguments) -> AgentToolReturn:
        absolute_path = arguments["file_path"]
        content = arguments["content"].strip("\n")
        start_line = arguments["start_line"]
        end_line = arguments.get("end_line", None)

        absolute_path = os.path.abspath(absolute_path)

        if not session.path_within_root(absolute_path):
            return AgentToolReturn.error(
                self.name,
                f"File {absolute_path} is not within the working directory {session.working_dir}",
            )
        if not os.path.exists(absolute_path):
            return AgentToolReturn.error(
                self.name,
                f"File {absolute_path} does not exist",
            )

        is_text, mime_type = is_text_file(absolute_path)
        if not is_text:
            return AgentToolReturn.error(
                self.name,
                f"File {absolute_path} is not a text file, the type is {mime_type}",
            )

        with open(absolute_path, "r") as f:
            lines = f.read().strip("\n")
            lines = lines.split("\n")

        if start_line > len(lines) + 1:
            return AgentToolReturn.error(
                self.name,
                f"Start line {start_line} is greater than the number of lines in the file {len(lines)}",
            )
        action = None
        edit_range = f"L{start_line}{f'-{end_line}' if end_line else ''}"
        if end_line is None:
            # inserting
            lines.insert(start_line - 1, content)
            action = "INSERT"
        elif content == "":
            # deleting
            lines = lines[: start_line - 1] + lines[end_line:]
            action = "DELETE"
        else:
            # replacing
            lines = lines[: start_line - 1] + content.split("\n") + lines[end_line:]
            action = "REPLACE"
        with open(absolute_path, "w") as f:
            f.write("\n".join(lines))

        return AgentToolReturn(
            for_llm=f"Edit File {absolute_path} successfully: {action} {edit_range}",
            for_human=f"Edit File {absolute_path} successfully[{action} {edit_range}]",
        )
