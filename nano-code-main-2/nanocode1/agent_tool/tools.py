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
from .util_tool.render_mermaid import MermaidRenderTool
from .Pyhton_Tool.ManageDependencies import ManageDependenciesTool
from .Pyhton_Tool.RunCommand import RunCommandTool
from .git_tool.clone_repo import CloneRepoTool
# from .git_tool.analyze_repo import AnalyzeRepoTool  # 已禁用分析工具

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
        MermaidRenderTool.init(),
    ]
)


PYTHON_TOOLS = ToolRegistry()
PYTHON_TOOLS.add_tools(
    [
        ManageDependenciesTool.init(),
        RunCommandTool.init(),
    ]
)


GIT_TOOLS = ToolRegistry()
GIT_TOOLS.add_tools(
    [
        CloneRepoTool.init(),
        # AnalyzeRepoTool.init(),  # 已禁用分析工具
    ]
)
