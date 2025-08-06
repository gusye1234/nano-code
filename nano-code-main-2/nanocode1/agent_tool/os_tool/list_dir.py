import os
from ..base import AgentToolDefine, AgentToolReturn
from ...core.session import Session


class ListDirTool(AgentToolDefine):
    @classmethod
    def init(cls, **kwargs):
        return cls(
            name="list_dir",
            description="""Lists the contents of a specified directory from the local filesystem. 
Shows files and subdirectories with their basic information like size and type.
Similar to the Unix 'ls' command.""",
            parameters_schema={
                "properties": {
                    "absolute_path": {
                        "description": "The absolute path to the directory to list (e.g., '/home/user/project/'). Relative paths are not supported. You must provide an absolute path.",
                        "type": "string",
                        "pattern": "^/",
                    },
                    # "show_hidden": {
                    #     "description": "Optional: Whether to show hidden files and directories (those starting with '.'). Defaults to False.",
                    #     "type": "boolean",
                    # },
                    # "show_details": {
                    #     "description": "Optional: Whether to show detailed information like file size, permissions, and modification time. Defaults to False.",
                    #     "type": "boolean",
                    # },
                },
                "required": ["absolute_path"],
                "type": "object",
            },
        )

    async def _execute(self, session: Session, arguments) -> AgentToolReturn:
        absolute_path = arguments["absolute_path"]
        absolute_path = os.path.abspath(absolute_path)
        show_hidden = True
        # show_details = arguments.get("show_details", False)

        if not session.path_within_root(absolute_path):
            return AgentToolReturn.error(
                self.name,
                f"Directory {absolute_path} is not within the working directory {session.working_dir}",
            )

        if not os.path.exists(absolute_path):
            return AgentToolReturn.error(
                self.name, f"Directory {absolute_path} does not exist"
            )

        if not os.path.isdir(absolute_path):
            return AgentToolReturn.error(
                self.name, f"Path {absolute_path} is not a directory"
            )

        try:
            raw_items = os.listdir(absolute_path)
        except PermissionError:
            return AgentToolReturn.error(
                self.name, f"Permission denied to read directory {absolute_path}"
            )

        # Filter hidden files if not requested
        if not show_hidden:
            raw_items = [item for item in raw_items if not item.startswith(".")]

        items = []

        for item in raw_items:
            abs_path = os.path.join(absolute_path, item)
            if session.ignore_path(abs_path):
                continue
            items.append(item)

        # Sort items (directories first, then files, both alphabetically)
        def sort_key(item):
            item_path = os.path.join(absolute_path, item)
            is_dir = os.path.isdir(item_path)
            return (not is_dir, item.lower())  # False sorts before True, so dirs first

        items.sort(key=sort_key)

        # Build the output
        output_lines = []
        total_files = 0
        total_dirs = 0

        for item in items:
            item_path = os.path.join(absolute_path, item)

            try:
                stat_info = os.stat(item_path)
                is_dir = os.path.isdir(item_path)

                if is_dir:
                    total_dirs += 1
                    item_type = "[dir]"
                else:
                    total_files += 1
                    item_type = "[file]"

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

                # Format permissions
                mode = stat_info.st_mode
                permissions = ""
                permissions += "r" if mode & 0o400 else "-"
                permissions += "w" if mode & 0o200 else "-"
                permissions += "x" if mode & 0o100 else "-"
                permissions += "r" if mode & 0o040 else "-"
                permissions += "w" if mode & 0o020 else "-"
                permissions += "x" if mode & 0o010 else "-"
                permissions += "r" if mode & 0o004 else "-"
                permissions += "w" if mode & 0o002 else "-"
                permissions += "x" if mode & 0o001 else "-"

                # Format modification time
                import time

                mtime = time.strftime(
                    "%Y-%m-%d %H:%M", time.localtime(stat_info.st_mtime)
                )
                output_lines.append(
                    f"{item_type} {permissions} {size_str:>8} {mtime} {item}"
                )

            except (OSError, PermissionError):
                # If we can't stat the item, just show it without details
                output_lines.append(f"[?]   {item} (stat failed)")

        # Create summary
        if not items:
            content = "Directory is empty."
        else:
            content = "\n".join(output_lines)

        summary = f"Total: {total_dirs} directories, {total_files} files"

        return AgentToolReturn(
            for_llm=f"[Listed directory {absolute_path}]\n{content}\n\n{summary}",
            for_human=f"Listed directory {absolute_path} - {summary}",
        )
