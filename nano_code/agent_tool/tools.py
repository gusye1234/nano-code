from .registry import ToolRegistry
from .os_tool import (
    create_file,
    list_dir,
    read_file,
    find_files,
    search_text,
    edit_file,
    mv_file_or_dir,
)
from .util_tool import add_tasks

OS_TOOLS = ToolRegistry()
OS_TOOLS.add_tools(
    [
        list_dir.ListDirTool.init(),
        read_file.ReadFileTool.init(),
        create_file.CreateFileTool.init(),
        edit_file.EditFileTool.init(),
        mv_file_or_dir.MoveFileOrDirTool.init(),
        find_files.FindFilesTool.init(),
        search_text.SearchTextTool.init(),
    ]
)


UTIL_TOOLS = ToolRegistry()
UTIL_TOOLS.add_tools(
    [
        add_tasks.AddTasksTool.init(),
    ]
)
