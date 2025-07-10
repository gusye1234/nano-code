from .registry import ToolRegistry
from .os_tool import list_dir, read_file, write_file, find_files, search_text
from .util_tool import add_tasks

OS_TOOLS = ToolRegistry()
OS_TOOLS.add_tools(
    [
        list_dir.ListDirTool.init(),
        read_file.ReadFileTool.init(),
        write_file.WriteFileTool.init(),
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
