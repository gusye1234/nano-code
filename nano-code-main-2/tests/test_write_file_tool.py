import os
import asyncio
import pytest
from unittest.mock import Mock
from nano_code.agent_tool.os_tool.create_file import CreateFileTool
from nano_code.agent_tool.base import AgentToolReturn


# Helper: create a mock Session
def make_mock_session(working_dir="/tmp/test_root"):
    session = Mock()
    session.working_dir = working_dir
    session.path_within_root.side_effect = lambda ap: ap.startswith(working_dir)
    return session


def test_write_file_success(tmp_path):
    file_path = tmp_path / "output.txt"
    content = "Hello, world!"
    session = make_mock_session(str(tmp_path))

    args = {"file_path": str(file_path), "content": content}
    tool = CreateFileTool.init()
    result = asyncio.run(tool._execute(session, args))
    assert isinstance(result, AgentToolReturn)
    assert "successfully" in result.for_llm
    assert file_path.read_text() == content


def test_write_file_outside_root(tmp_path):
    fake_root = str(tmp_path)
    outside_file = os.path.join("/tmp", "definitely_outside.txt")
    session = make_mock_session(fake_root)
    args = {"file_path": outside_file, "content": "X"}
    tool = CreateFileTool.init()
    result = asyncio.run(tool._execute(session, args))
    assert (
        "not within the working directory" in result.for_llm
        or "not within the working directory" in result.for_human
    )
