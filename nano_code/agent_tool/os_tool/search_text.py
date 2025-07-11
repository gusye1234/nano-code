import os
import glob
import re
from typing import List, Optional
from dataclasses import dataclass
from ...constants import MAX_READ_FILE_LINES, MAX_LINE_CHAR_LENGTH
from ..base import AgentToolDefine, AgentToolReturn
from ...core.session import Session
from ...utils.file import is_text_file


@dataclass
class GrepMatch:
    file_path: str
    line_number: int
    line: str
    section: str


class SearchTextTool(AgentToolDefine):
    @classmethod
    def init(cls, **kwargs):
        return cls(
            name="search_text",
            description="""Searches for a regular expression pattern within the content of files in a specified directory (or current working directory). 
Can filter files by a glob pattern. Returns the lines containing matches, along with their file paths and line numbers.""",
            parameters_schema={
                "properties": {
                    "pattern": {
                        "description": "The regular expression (regex) pattern to search for within file contents (e.g., 'function\\s+myFunction', 'import\\s+\\{.*\\}\\s+from\\s+.*').",
                        "type": "string",
                    },
                    "path": {
                        "description": "Optional: The absolute path to the directory to search within. If omitted, searches the current working directory.",
                        "type": "string",
                    },
                    "include": {
                        "description": "Optional: A glob pattern to filter which files are searched (e.g., '*.js', '*.{ts,tsx}', 'src/**'). If omitted, searches all files (respecting potential global ignores).",
                        "type": "string",
                    },
                    "max_matches": {
                        "description": "Optional: The maximum number of matches to return. Default is 50",
                        "type": "integer",
                    },
                },
                "required": ["pattern"],
                "type": "object",
            },
        )

    def _perform_search(
        self,
        pattern: str,
        search_path: str,
        include: Optional[str] = None,
        session: Session = None,
        section_lines=2,
    ) -> List[GrepMatch]:
        """Perform search using pure Python implementation."""
        matches = []

        # Determine glob pattern
        glob_pattern = include

        try:
            # Use glob to find files
            matched_files = glob.glob(
                glob_pattern, root_dir=search_path, recursive=True
            )

            # Compile regex pattern
            regex = re.compile(pattern, re.IGNORECASE)

            for file_path in matched_files:
                abs_file_path = os.path.join(search_path, file_path)

                # Skip if not a file
                if not os.path.isfile(abs_file_path):
                    continue

                # Skip ignored paths
                if session and session.ignore_path(abs_file_path):
                    continue

                # Skip binary files
                try:
                    is_text, _ = is_text_file(abs_file_path)
                    if not is_text:
                        continue
                except Exception:
                    continue

                try:
                    with open(
                        abs_file_path, "r", encoding="utf-8", errors="ignore"
                    ) as f:
                        lines = []
                        for i, l in enumerate(f):
                            if i > MAX_READ_FILE_LINES:
                                break
                            lines.append(l.rstrip("\n\r"))
                    skip_to = None
                    for line_num, line in enumerate(lines):
                        if skip_to is not None:
                            if line_num < skip_to:
                                continue
                            skip_to = None
                        if regex.search(line):
                            start_line = max(0, line_num - section_lines)
                            end_line = min(len(lines), line_num + section_lines)
                            matches.append(
                                GrepMatch(
                                    file_path=abs_file_path,
                                    line_number=line_num + 1,
                                    line=(
                                        line
                                        if len(line) < MAX_LINE_CHAR_LENGTH
                                        else line[:MAX_LINE_CHAR_LENGTH]
                                        + "... [truncated]"
                                    ),
                                    section="\n".join(
                                        [
                                            f"L{line_i+1} "
                                            + (
                                                l
                                                if len(l) < MAX_LINE_CHAR_LENGTH
                                                else l[:MAX_LINE_CHAR_LENGTH]
                                                + "... [truncated]"
                                            )
                                            for line_i, l in zip(
                                                range(start_line, end_line),
                                                lines[start_line:end_line],
                                            )
                                        ]
                                    ),
                                )
                            )
                            skip_to = end_line
                except Exception:
                    # Skip files that can't be read
                    continue

        except Exception as e:
            raise Exception(f"Search failed: {str(e)}")

        return matches

    async def _execute(self, session: Session, arguments) -> AgentToolReturn:
        pattern = arguments["pattern"]
        search_path = arguments.get("path", session.working_dir)
        include = arguments.get("include", "**/*")
        max_matches = arguments.get("max_matches", 50)
        # Normalize the search path
        search_path = os.path.abspath(search_path)

        # Validate the search path is within the working directory
        if not session.path_within_root(search_path):
            return AgentToolReturn.error(
                self.name,
                f"Search path {search_path} is not within the working directory {session.working_dir}",
            )

        # Check if the search path exists
        if not os.path.exists(search_path):
            return AgentToolReturn.error(
                self.name, f"Search path {search_path} does not exist"
            )

        # Check if the search path is a directory
        if not os.path.isdir(search_path):
            return AgentToolReturn.error(
                self.name, f"Search path {search_path} is not a directory"
            )

        try:
            matches = self._perform_search(pattern, search_path, include, session)
        except Exception as e:
            return AgentToolReturn.error(
                self.name, f"Error during text search: {str(e)}"
            )

        # Format output
        if not matches:
            content = ""
            summary = f"0 matches found for pattern {pattern}"
        else:
            output_lines = []
            for match in matches[
                :max_matches
            ]:  # Limit to max_matches to avoid overwhelming output
                # Truncate long lines
                line_content = match.line
                if len(line_content) > MAX_LINE_CHAR_LENGTH:
                    line_content = (
                        line_content[:MAX_LINE_CHAR_LENGTH] + "... [truncated]"
                    )

                output_lines.append(
                    f"{match.file_path}:L{match.line_number}\n{match.section}\n"
                )

            content = "\n".join(output_lines)
            total_matches = len(matches)
            shown_matches = min(total_matches, max_matches)

            if total_matches > max_matches:
                summary = f"Found {total_matches} matches (showing first {shown_matches}) for pattern '{pattern}'"
            else:
                summary = f"Found {total_matches} matches for pattern '{pattern}'"

        return AgentToolReturn(
            for_llm=f"[Text search results for pattern '{pattern}' in {search_path}, return content with line annotations]\n{content}\n\n{summary}",
            for_human=summary,
        )
