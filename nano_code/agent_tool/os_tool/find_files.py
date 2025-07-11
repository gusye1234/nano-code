import os
import glob
import time
from ...constants import MAX_READ_FILE_LINES, MAX_LINE_CHAR_LENGTH
from ..base import AgentToolDefine, AgentToolReturn
from ...core.session import Session
from ...utils.file import is_text_file


class FindFilesTool(AgentToolDefine):
    @classmethod
    def init(cls, **kwargs):
        return cls(
            name="find_files",
            description="""Efficiently finds files matching specific glob patterns (e.g., `src/**/*.ts`, `**/*.md`), returning absolute paths sorted by modification time (newest first). 
Ideal for quickly locating files based on their name or path structure, especially in large codebases.""",
            parameters_schema={
                "properties": {
                    "pattern": {
                        "description": "The glob pattern to match against (e.g., '**/*.py', 'docs/*.md'). The pattern is case-sensitive.",
                        "type": "string",
                    },
                    "path": {
                        "description": "Optional: The absolute path to the directory to search within. If omitted, searches the root directory.",
                        "type": "string",
                    },
                    "respect_git_ignore": {
                        "description": "Optional: Whether to respect .gitignore patterns when finding files. Only available in git repositories. Defaults to true.",
                        "type": "boolean",
                    },
                },
                "required": ["pattern"],
                "type": "object",
            },
        )

    async def _execute(self, session: Session, arguments) -> AgentToolReturn:
        pattern = arguments["pattern"]
        path = arguments.get("path", session.working_dir)
        respect_git_ignore = arguments.get("respect_git_ignore", True)

        # Normalize the search path
        search_path = os.path.abspath(path)

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
            # Use glob to find matching files with root_dir parameter
            matched_files = glob.glob(pattern, recursive=True, root_dir=search_path)
            # Convert to absolute paths and filter
            results = []
            for file_path in matched_files:
                abs_path = os.path.join(search_path, file_path)

                # Skip if not a file
                if not os.path.isfile(abs_path):
                    continue

                # Respect git ignore if requested
                if respect_git_ignore and session.ignore_path(abs_path):
                    continue

                results.append(abs_path)

        except Exception as e:
            return AgentToolReturn.error(
                self.name, f"Error during file search: {str(e)}"
            )

        # Sort by modification time (newest first)
        try:
            results.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        except Exception:
            # If there's an issue getting modification times, fall back to alphabetical sorting
            results.sort()

        # Build the output
        if not results:
            content = ""
            summary = "0 files found"
        else:
            output_lines = []

            for file_path in results:
                try:
                    stat_info = os.stat(file_path)

                    # Format file size
                    size = stat_info.st_size
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024 * 1024:
                        size_str = f"{size/1024:.1f}KB"
                    elif size < 1024 * 1024 * 1024:
                        size_str = f"{size/(1024*1024):.1f}MB"
                    else:
                        size_str = f"{size/(1024*1024*1024):.1f}GB"

                    # Format modification time
                    mtime = time.strftime(
                        "%Y-%m-%d %H:%M", time.localtime(stat_info.st_mtime)
                    )

                    output_lines.append(f"{size_str:>8} {mtime} {file_path}")

                except (OSError, PermissionError):
                    # If we can't stat the file, just show the path
                    output_lines.append(f"{'?':>8} {'?':>16} {file_path}")

            content = "\n".join(output_lines)
            summary = f"Found {len(results)} files matching pattern '{pattern}'"

        return AgentToolReturn(
            for_llm=f"[Found files matching pattern '{pattern}' in {search_path}]\n{content}\n\n{summary}",
            for_human=f"Found {len(results)} files matching pattern '{pattern}'",
        )
