import os
import asyncio
import pytest
from unittest.mock import Mock, patch
from nano_code.agent_tool.os_tool.read_file import ReadFileTool
from nano_code.agent_tool.base import AgentToolReturn

# Helper: create a mock Session
def make_mock_session(working_dir="/tmp/test_root"):
    session = Mock()
    session.working_dir = working_dir
    session.path_within_root.side_effect = lambda ap: ap.startswith(working_dir)
    return session

# Basic file read test
def test_read_file_success(tmp_path):
    # Create a text file
    file_path = tmp_path / "test.txt"
    file_path.write_text("A\nB\nC\nD")
    session = make_mock_session(str(tmp_path))

    # Patch is_text_file to always return True (text), and patch os.path.exists/isfile
    with patch("nano_code.agent_tool.os_tool.read_file.is_text_file", return_value=(True, "text/plain")):
        args = {"absolute_path": str(file_path), "offset": 1, "limit": 2}
        tool = ReadFileTool.init()
        result = asyncio.run(tool._execute(session, args))
        assert isinstance(result, AgentToolReturn)
        assert "L1 B" in result.for_llm
        assert "L2 C" in result.for_llm
        assert "Read File" in result.for_human

# File does not exist
def test_read_file_not_exist(tmp_path):
    session = make_mock_session(str(tmp_path))
    missing_path = str(tmp_path / "missing.txt")
    with patch("nano_code.agent_tool.os_tool.read_file.is_text_file", return_value=(True, "text/plain")):
        args = {"absolute_path": missing_path}
        tool = ReadFileTool.init()
        result = asyncio.run(tool._execute(session, args))
        assert "does not exist" in result.for_llm or "does not exist" in result.for_human
