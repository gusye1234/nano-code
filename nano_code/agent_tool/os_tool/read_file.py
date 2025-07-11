import os
from ...constants import MAX_READ_FILE_LINES, MAX_LINE_CHAR_LENGTH
from ..base import AgentToolDefine, AgentToolReturn
from ...core.session import Session
from ...utils.file import is_text_file


class ReadFileTool(AgentToolDefine):
    @classmethod
    def init(cls, **kwargs):
        return cls(
            name="read_file",
            description="""Reads and returns the content of a specified file with line annotations from the local filesystem. 
ONLY handles text files(e.g. .txt, .md, .py, .js, .css, .html, .json, .yaml...). 
For text files, it can read specific line ranges.""",
            parameters_schema={
                "properties": {
                    "absolute_path": {
                        "description": "The absolute path to the file to read (e.g., '/home/user/project/file.txt'). Relative paths are not supported. You must provide an absolute path.",
                        "type": "string",
                        "pattern": "^/",
                    },
                    "offset": {
                        "description": "Optional: For text files, the 0-based line number to start reading from. Requires 'limit' to be set. Use for paginating through large files.",
                        "type": "number",
                    },
                    "limit": {
                        "description": "Available options: [50, 100, 200,...] For text files, maximum number of lines to read. Use with 'offset' to paginate through large files. If omitted, reads the entire file (if feasible, up to a default limit).",
                        "type": "number",
                    },
                },
                "required": ["absolute_path"],
                "type": "object",
            },
        )

    async def _execute(self, session: Session, arguments) -> AgentToolReturn:
        absolute_path = arguments["absolute_path"]
        offset = arguments.get("offset", 0)
        limit = arguments.get("limit", 200)

        absolute_path = os.path.abspath(absolute_path)

        if offset is not None and offset < 0:
            return AgentToolReturn.error(
                self.name, "Offset must be a non-negative integer"
            )
        if limit is not None and limit <= 0:
            return AgentToolReturn.error(self.name, "Limit must be a positive integer")

        if not session.path_within_root(absolute_path):
            return AgentToolReturn.error(
                self.name,
                f"File {absolute_path} is not within the working directory {session.working_dir}",
            )
        if not os.path.exists(absolute_path):
            return AgentToolReturn.error(
                self.name, f"File {absolute_path} does not exist"
            )
        if not os.path.isfile(absolute_path):
            return AgentToolReturn.error(
                self.name, f"File {absolute_path} is not a file"
            )

        is_text, mime_type = is_text_file(absolute_path)
        if not is_text:
            return AgentToolReturn.error(
                self.name,
                f"File {absolute_path} is not a text file, the type is {mime_type}",
            )

        with open(absolute_path, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.split("\n")
        total_lines = len(lines)

        start_line_no = offset or 0
        end_line_no = min(
            start_line_no + limit if limit else len(lines), MAX_READ_FILE_LINES
        )

        actual_start_line_no = min(start_line_no, len(lines))
        actual_end_line_no = max(min(end_line_no, len(lines)), actual_start_line_no)
        read_lines = lines[actual_start_line_no:actual_end_line_no]
        line_nos = [f"L{i+1}" for i in range(actual_start_line_no, actual_end_line_no)]
        read_lines = [
            (
                l
                if len(l) < MAX_LINE_CHAR_LENGTH
                else l[:MAX_LINE_CHAR_LENGTH] + "... [truncated]"
            )
            for l in read_lines
        ]
        content = "\n".join([f"{i} {l}" for i, l in zip(line_nos, read_lines)])
        return AgentToolReturn(
            for_llm=f"""[Read File {absolute_path} with L{actual_start_line_no}-{actual_end_line_no}. #total lines {total_lines}. below is the file content with line annotations]
{content}
""",
            for_human=f"Read File {absolute_path} with L{actual_start_line_no}-{actual_end_line_no}.",
        )
