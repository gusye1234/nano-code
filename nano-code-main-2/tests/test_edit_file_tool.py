import os
import asyncio
import tempfile
from nano_code.agent_tool.os_tool.edit_file import EditFileTool
from nano_code.core.session import Session

import os
import asyncio
import tempfile
from nano_code.agent_tool.os_tool.edit_file import EditFileTool
from nano_code.core.session import Session
import pytest


@pytest.mark.asyncio
async def test_edit_file_tool_insert_replace_delete():
    # Create temp file and session
    with tempfile.NamedTemporaryFile(delete=False, mode="w+", suffix=".txt") as tmp:
        tmp.write("line1\nline2\nline3\n")
        tmp_path = tmp.name
    session = Session(working_dir=os.path.dirname(tmp_path))
    tool = EditFileTool.init()

    # Insert a line before line 2
    args_insert = {"file_path": tmp_path, "content": "inserted_line", "start_line": 2}
    r = await tool.execute(session, args_insert)
    with open(tmp_path) as f:
        lines = f.readlines()
    print("After insert:", lines, r)
    assert lines == ["line1\n", "inserted_line\n", "line2\n", "line3"]

    # Replace line 2 with something else
    args_replace = {
        "file_path": tmp_path,
        "content": "replaced_line\n",
        "start_line": 2,
        "end_line": 2,
    }
    await tool._execute(session, args_replace)
    with open(tmp_path) as f:
        lines = f.readlines()
    print("After replace:", lines)
    assert lines == ["line1\n", "replaced_line\n", "line2\n", "line3"]

    # Delete lines 2-3
    args_delete = {"file_path": tmp_path, "content": "", "start_line": 2, "end_line": 3}
    await tool._execute(session, args_delete)
    with open(tmp_path) as f:
        lines = f.readlines()
    print("After delete:", lines)
    assert lines == ["line1\n", "line3"]

    os.remove(tmp_path)


@pytest.mark.asyncio
async def test_edit_file_tool_edge_cases():
    # Create temp file and session
    with tempfile.NamedTemporaryFile(delete=False, mode="w+", suffix=".txt") as tmp:
        tmp.write("a\nb\nc\n")
        tmp_path = tmp.name
    session = Session(working_dir=os.path.dirname(tmp_path))
    tool = EditFileTool.init()

    # 1. Append a line at the end
    args_append = {"file_path": tmp_path, "content": "d", "start_line": 4}
    r = await tool.execute(session, args_append)
    with open(tmp_path) as f:
        lines = f.readlines()
    print("After append:", lines, r)
    assert lines == ["a\n", "b\n", "c\n", "d"]

    # 2. Replace the entire content
    args_replace_all = {
        "file_path": tmp_path,
        "content": "x\ny\n",
        "start_line": 1,
        "end_line": 4,
    }
    await tool.execute(session, args_replace_all)
    with open(tmp_path) as f:
        lines = f.readlines()
    assert lines == ["x\n", "y"]

    # 3. No-op (replace line with itself, empty content)
    args_noop = {"file_path": tmp_path, "content": "", "start_line": 1, "end_line": 1}
    await tool.execute(session, args_noop)
    with open(tmp_path) as f:
        lines = f.readlines()
    assert lines == ["y"]

    # 4. Out-of-range line number (should not change content)
    args_out_of_range = {"file_path": tmp_path, "content": "z", "start_line": 100}
    try:
        await tool.execute(session, args_out_of_range)
    except Exception:
        pass  # Depending on implementation, might raise error. Accept both behaviors.
    with open(tmp_path) as f:
        lines = f.readlines()
    assert lines == ["y"]

    # 5. Delete entire file
    args_delete_all = {
        "file_path": tmp_path,
        "content": "",
        "start_line": 1,
        "end_line": 2,
    }
    await tool.execute(session, args_delete_all)
    with open(tmp_path) as f:
        lines = f.readlines()
    assert lines == []

    os.remove(tmp_path)
